"""
Primary Scraping module 
"""
from requests_html import HTMLSession 
from bs4 import BeautifulSoup as bs

MIN_VIEWS = 10000
LIKE_FACTOR = 100

def scrape_content(URL):
    """
    Method to validate a URL based on certain criterias
    """
    session = HTMLSession()
    response = session.get(URL)
    # Execute the JS in the page
    response.html.render(sleep=1,timeout=20)

    soup = bs(response.html.html, "html.parser")
    text_yt_formatted_strings = soup.find_all("yt-formatted-string", {"id": "text", "class": "ytd-toggle-button-renderer"})
    try:
        views = int(''.join([char for char in soup.find("span", attrs={"class": "view-count"}).text if char.isdigit()]))
        likes = int(''.join([char for char in text_yt_formatted_strings[0].attrs.get("aria-label") if char.isdigit()]))
        dislikes = int(''.join([char for char in text_yt_formatted_strings[1].attrs.get("aria-label") if char.isdigit()]))

        print("URL: {},Views: {}, Likes: {}, Dislikes: {}".format(URL, views, likes, dislikes))
        return True if (views >= MIN_VIEWS and likes >= LIKE_FACTOR*dislikes) else False

    except Exception as e:
        print("Scraping did'nt work for: {} because of error: {}".format(URL, e))

