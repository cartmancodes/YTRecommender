"""
Utility/Constants module for the script
"""
from functools import wraps
from bs4 import BeautifulSoup as bs

MIN_VIEWS = 10000
LIKE_FACTOR = 100

def timer(func):
    """Decorator for timer utility"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        print("Fetching started for {}".format(args[1]))
        output =  await func(*args, **kwargs)
        print("Fetching ended for {}".format(args[1]))
        return output
    return wrapper


def validate_content(response, url):
    """Method to validate quality of our URL content"""
    soup = bs(response.html.html, "html.parser")
    text_yt_formatted_strings = soup.find_all("yt-formatted-string", {"id": "text", "class": "ytd-toggle-button-renderer"})
    try:
        like_index = 0 if "likes" in str(text_yt_formatted_strings[0]) else 1
        views = int(''.join([char for char in soup.find("span", attrs={"class": "view-count"}).text if char.isdigit()]))
        likes = int(''.join([char for char in text_yt_formatted_strings[like_index].attrs.get("aria-label") if char.isdigit()]))
        dislikes = int(''.join([char for char in text_yt_formatted_strings[like_index + 1].attrs.get("aria-label") if char.isdigit()]))
        print("URL: {},Views: {}, Likes: {}, Dislikes: {}".format(url, views, likes, dislikes))
        return url if (views >= MIN_VIEWS and likes >= LIKE_FACTOR*dislikes) else None
    except Exception as e:
        print("Scraping did'nt work for: {} because of error: {}".format(url, e))