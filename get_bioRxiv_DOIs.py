#!/usr/bin/python
# -*- coding: utf-8 -*-

# Paranoid steps to make sure Python uses UTF-8 encoding
import sys
reload(sys)
sys.setdefaultencoding("utf-8")

import codecs # More UTF-8 paranoia
import requests # For loading web pages
from datetime import timedelta, date # Standard Python packages for working with dates
from bs4 import BeautifulSoup as bs # Popular HTML parser
from slugify import slugify # Converts arbitrary strings into nice filenames
import pickle # Package any data structure to be written to/read from a file
import time # Necessary to sleep
import os # Standard operating system actions (check if file exists, etc.)

# An example search URL:
# http://biorxiv.org/search/limit_from%3A2017-01-01%20limit_to%3A2017-01-02%20numresults%3A10%20sort%3Arelevance-rank%20format_result%3Astandard
searchTemplate = 'http://biorxiv.org/search/%20limit_from%3A{}%20limit_to%3A{}%20numresults%3A200%20sort%3Apublication-date%20direction%3Aascending%20format_result%3Astandard'

# Download and cache a webpage if it hasn't been downloaded and cached before
# NOTE: Requires the existence of a folder named 'searchPages'!
def cacheQuery(query, forceUncache=False):
  queryFile = 'searchPages/' + slugify(query)
  if ((not forceUncache) and os.path.isfile(queryFile)):
    data = pickle.load(open(queryFile, 'rb'))
  else:
    time.sleep(1) # Waiting 1 second is the minimum level of "politeness"
    r = requests.get(query)
    if (r.status_code == 200):
      data = r.text
      pickle.dump(data, open(queryFile, 'wb'))  
    else:
      data = None
  return data

# Parse each search page for article listings
def processSearchPage(page, query):

  articleData = {} # The article listings for this page, indexed by DOI

  html = bs(page, "lxml") # Initialize BeautifulSoup parser with lxml parsing module

  articles = html.find_all('li', attrs={'class': 'search-result'})
  for article in articles:

    # Get the item header 
    citation = article.find('div', attrs={'class': 'highwire-article-citation'})
    master_version = citation.get('data-pisa-master')
    version = citation.get('data-pisa')
    atom_path = citation.get('data-apath')

    # Get the DOI
    doispan = article.find('span', attrs={'class': 'highwire-cite-metadata-doi'})
    doi = doispan.text.strip().replace('doi: https://', '')
    
    # Get the title info
    title = article.find('span', attrs={'class': 'highwire-cite-title'})
    title = title.text.strip().replace("\n", "")

    # Now collect author information
    authors = article.find_all('span', attrs={'class': 'highwire-citation-author'})
    all_authors = []
    for author in authors:
      all_authors.append(author.text)

    author_list = '|'.join(all_authors)
    outdata = [version, title, atom_path, author_list]
    
    articleData[doi] = outdata
    
  return articleData

# Call the functions above to open a search page and parse its contents
def getDOIsInRange(startDate, endDate):

  global outfile
    
  queryString = searchTemplate.format(startDate, endDate)
  page = cacheQuery(queryString)

  if (page is not None):
    print "searching " + queryString
    pageArticles = processSearchPage(page, queryString)
    
    # Write all the DOI info to a file
    for doi in pageArticles:
      outfile.write(str(doi) + "\t" + "\t".join(pageArticles[doi]) + "\n")

# MAIN starts here

outfile = codecs.open("biorxiv_dois.txt", 'w', 'utf-8')

start_date = date(2013, 11, 6)
end_date = date(2017, 5, 7)

# Set the start and end of the date interval to be 1 day apart
d = start_date
delta = timedelta(days=1)

# Step through the full date range, incrementing the start and end
# day by 1 each time
while d <= end_date:
  searchDate = d.strftime("%Y-%m-%d")
  print("searching date " + searchDate)
  getDOIsInRange(searchDate, searchDate)
  d += delta

outfile.close()
