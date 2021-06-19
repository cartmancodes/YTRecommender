"""
Primary Scraping module 
"""
from asyncio import tasks
from asyncio.events import get_event_loop
from requests_html import AsyncHTMLSession
from concurrent.futures import ThreadPoolExecutor
from bs4 import BeautifulSoup as bs
import time
import asyncio

MIN_VIEWS = 10000
LIKE_FACTOR = 100

def scrape_content(urls):
    # Asyncio's run() does'nt play well with request-html's arender(), hence use event loops
    loop = asyncio.get_event_loop()
    future = asyncio.ensure_future(get_tasks(urls))
    response_list = loop.run_until_complete(future)
    interested_contents = [validate_content(response, url) for response, url in response_list]
    interested_contents = list(filter(None, interested_contents))
    # Check and close event loops explicitly
    if loop.is_running():
        loop.close()

    return interested_contents

async def get_tasks(urls):
    """
    Method to validate a URLs based on certain criterias
    """
    session = AsyncHTMLSession()
    tasks = [get_response(session, url) for url in urls]
    content_list = await asyncio.gather(*tasks)
    await session.close()
    return content_list

async def get_response(session, url):
    print("Fetching initiated for url: {}".format(url))
    response = await session.get(url)
    await response.html.arender(timeout=25)
    print("Fetching completed for url: {}".format(url))
    return (response, url)

def validate_content(response, url):
    soup = bs(response.html.html, "html.parser")
    text_yt_formatted_strings = soup.find_all("yt-formatted-string", {"id": "text", "class": "ytd-toggle-button-renderer"})
    try:
        views = int(''.join([char for char in soup.find("span", attrs={"class": "view-count"}).text if char.isdigit()]))
        likes = int(''.join([char for char in text_yt_formatted_strings[0].attrs.get("aria-label") if char.isdigit()]))
        dislikes = int(''.join([char for char in text_yt_formatted_strings[1].attrs.get("aria-label") if char.isdigit()]))
        print("URL: {},Views: {}, Likes: {}, Dislikes: {}".format(url, views, likes, dislikes))
        
        return url if (views >= MIN_VIEWS and likes >= LIKE_FACTOR*dislikes) else None
    except Exception as e:
        print("Scraping did'nt work for: {} because of error: {}".format(url, e))