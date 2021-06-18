"""
Primary Scraping module 
"""
from asyncio import tasks
from asyncio.events import get_event_loop
from requests_html import AsyncHTMLSession 
from bs4 import BeautifulSoup as bs
import time
import asyncio

MIN_VIEWS = 10000
LIKE_FACTOR = 100

async def scrape_content(urls):
    """
    Method to validate a URLs based on certain criterias
    """
    interested_urls, interested_responses, tasks = [], [], []
    start_time = time.time()
    
    loop = asyncio.get_event_loop()
    for url in urls:        
        tasks.append(loop.create_task(fetch_url(url)))
    loop.run_until_complete(asyncio.wait(tasks))
    loop.close()

    for response in interested_responses:
        if validate_content(response, url):
            interested_urls.append(urls)
    
    end_time = time.time()
    print("Time Taken: " + str(end_time - start_time))
    return interested_urls


async def fetch_url(url):
    print("Fetch URL invocsted for url: {}".format(url))
    session = AsyncHTMLSession()
    response = await session.get(url)
    # Execute JS in the page
    return await response.html.render(asyncio.sleep(2), timeout=20)

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