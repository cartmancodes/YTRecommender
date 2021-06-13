"""
Primary scraper module
"""
import requests
from youtubesearchpython import VideosSearch
from bs4 import BeautifulSoup


# Monkey Patching security cerificate 
import ssl
ssl._create_default_https_context = ssl._create_unverified_context

MIN_VIEWS = 20000
LIKE_FACTOR = 100

class Scraper:
    def __init__(self, opts):
        self.content = opts.content
        self.pages = opts.pages
    
    def get_content(self):
        contents = self.search_content()

    def search_content(self):
        return VideosSearch(self.content, limit=self.pages)

    def prune_content(self, contents):
        interested_contents = []
        for content in contents:
            interested_contents.append(self.validate_content(content['URL']))

    def validate_content(self, URL):
        r = requests.get(URL)
        s = BeautifulSoup(r.text, 'html.parser')
        
        # Scrape views, like and dislikes
        views = s.find("div", class_="watch-view-count").text
        likes = s.find("span", class_="like-button-renderer").span.button.text
        dislikes = s.find("span", class_="dislike-button-renderer").span.button.text
        
        if (views > MIN_VIEWS and likes > dislikes * LIKE_FACTOR):
            return True
        else:
            return False

