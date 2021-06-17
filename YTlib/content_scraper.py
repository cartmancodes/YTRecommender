"""
Primary Scraping module 
"""
from requests_html import HTMLSession 
from bs4 import BeautifulSoup as bs

MIN_VIEWS = 10000
LIKE_FACTOR = 100

def scrape_content(urls):
    """
    Method to validate a URLs based on certain criterias
    """
    interested_urls= []
    for url in urls:        
        session = HTMLSession()
        response = session.get(url)
        # Execute the JS in the page
        response.html.render(sleep=2,timeout=20)
        if validate_content(response, url):
            interested_urls.append(urls)
    
    return interested_urls
        

def validate_content(response, url):
    soup = bs(response.html.html, "html.parser")
    text_yt_formatted_strings = soup.find_all("yt-formatted-string", {"id": "text", "class": "ytd-toggle-button-renderer"})
    try:
        views = int(''.join([char for char in soup.find("span", attrs={"class": "view-count"}).text if char.isdigit()]))
        likes = int(''.join([char for char in text_yt_formatted_strings[0].attrs.get("aria-label") if char.isdigit()]))
        dislikes = int(''.join([char for char in text_yt_formatted_strings[1].attrs.get("aria-label") if char.isdigit()]))
        
        print("URL: {},Views: {}, Likes: {}, Dislikes: {}".format(url, views, likes, dislikes))
        return True if (views >= MIN_VIEWS and likes >= LIKE_FACTOR*dislikes) else False

    except Exception as e:
        print("Scraping did'nt work for: {} because of error: {}".format(url, e))