"""
Primary Validator module
"""
import asyncio
from youtubesearchpython import VideosSearch
from bs4 import BeautifulSoup
from content_scraper import scrape_content

# Monkey patching code 
import ssl
ssl._create_default_https_context = ssl._create_unverified_context

class ContentGetter:
    def __init__(self, opts):
        self.content = opts.content
        self.pages = opts.pages
    
    def get_content(self):
        contents = self.search_content()
        return self.prune_content(contents.result()['result'])

    def search_content(self):
        return VideosSearch(self.content, limit=self.pages)

    def prune_content(self, contents):        
        urls = [content['link'] for content in contents]
        return asyncio.run(scrape_content(urls))
        #return scrape_content(urls)



