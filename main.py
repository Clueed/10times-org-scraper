from bs4 import BeautifulSoup
import requests
import asyncio
import aiohttp

url = "https://10times.com/events"
page = requests.get(url)

soup = BeautifulSoup(page.text, "html.parser")

events = soup.find_all("a", attrs={"data-ga-category": "Event Listing"})

eventurls = []
for event in events:
    eventurls.append(event["href"])

print(eventurls)

async def fetch(session, url):
    async with session.get(url) as response:
        if response.status != 200:
            response.raise_for_status()
        return await response.text()


async def fetch_all(session, urls):
    tasks = []
    for url in urls:
        task = asyncio.create_task(fetch(session, url))
        tasks.append(task)
    results = await asyncio.gather(*tasks)
    return results


async def main():
    urls = eventurls[0:1]
    async with aiohttp.ClientSession() as session:
        htmls = await fetch_all(session, urls)
        return htmls



