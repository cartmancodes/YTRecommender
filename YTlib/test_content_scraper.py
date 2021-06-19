import unittest

class ContentScraper(unittest.TestCase):
    async def test_contet_scraper(self):
        from content_scraper import fetch_url
        op =  await fetch_url("https://www.youtube.com/watch?v=xizN47Box_Y")
        self.assertIsNotNone(op)

if __name__ == "__main__":
    await unittest.main()