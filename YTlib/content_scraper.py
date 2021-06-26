"""
Primary Scraping module 
"""
from asyncio import tasks
from asyncio.events import get_event_loop
from requests_html import AsyncHTMLSession
from concurrent.futures import ThreadPoolExecutor
import time
import asyncio
from utils import timer, MIN_VIEWS, LIKE_FACTOR, validate_content

def scrape_content(urls):
    # Asyncio's run() does'nt play well with request-html's arender(), hence using event loops
    loop = asyncio.get_event_loop()
    future = asyncio.ensure_future(get_tasks(urls))
    response_list = loop.run_until_complete(future)
    interested_contents = [validate_content(response, url) for response, url in response_list]
    # Check and close event loops explicitly
    if loop.is_running():
        loop.close()

    return list(filter(None, interested_contents))

async def get_tasks(urls):
    """Method to validate a URLs based on certain criterias"""
    session = AsyncHTMLSession()
    tasks = [get_response(session, url) for url in urls]
    content_list = await asyncio.gather(*tasks)
    await session.close()
    return content_list

@timer
async def get_response(session, url):
    response = await session.get(url)
    # Render JS code 
    await response.html.arender(sleep=4,timeout=30)
    return (response, url)



        

