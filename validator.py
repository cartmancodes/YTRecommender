"""
Primary validating module 
"""

from requests_html import HTMLSession 
from bs4 import BeautifulSoup as bs

# Monkey Patching security cerificate 
# import ssl
# ssl._create_default_https_context = ssl._create_unverified_context

MIN_VIEWS = 20000
LIKE_FACTOR = 100

def validate_content(URL):
    """
    Method to validate a URL based on certain criterias
    """

    session = HTMLSession()
    response = session.get(URL)
    # Execute the JS in the page
    response.html.render()

    soup = bs(response.html.html, "html.parser")
    text_yt_formatted_strings = soup.find_all("yt-formatted-string", {"id": "text", "class": "ytd-toggle-button-renderer"})

    views = int(''.join([char for char in soup.find("span", attrs={"class": "view-count"}).text if char.isdigit()]))
    likes = int(''.join([char for char in text_yt_formatted_strings[0].attrs.get("aria-label") if char.isdigit()]))
    dislikes = int(''.join([char for char in text_yt_formatted_strings[1].attrs.get("aria-label") if char.isdigit()]))
    