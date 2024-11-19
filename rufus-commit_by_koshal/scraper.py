import aiohttp
import asyncio
from bs4 import BeautifulSoup
import urllib.parse

async def fetch(session, url):
    async with session.get(url) as response:
        return await response.text()

def is_relevant_link(link, keywords):
    href = link['href']
    text = link.get_text()
    return any(keyword in href or keyword in text for keyword in keywords)

async def scrape_website(url, depth=1, keywords=None, instructions=None):
    if depth < 1:
        return {}

    async with aiohttp.ClientSession() as session:
        try:

            html = await fetch(session, url)
            soup = BeautifulSoup(html, 'html.parser')


            main_content = soup.get_text()
            is_relevant = (
                any(keyword in main_content for keyword in keywords or []) 
                or (instructions and instructions.lower() in main_content.lower())
            )


            data = {
                'url': url,
                'title': soup.title.string if soup.title else '',
                'content': main_content if is_relevant else '',
                'links': []
            }


            links = soup.find_all('a', href=True)
            for link in links:
                href = link['href']
                if not href.startswith('http'):  
                    href = urllib.parse.urljoin(url, href)
                
                if not keywords or is_relevant_link(link, keywords):
                    data['links'].append(href)


            if depth > 1 and is_relevant:
                nested_data = await asyncio.gather(
                    *[scrape_website(link, depth - 1, keywords, instructions) for link in data['links']]
                )
                data['nested_links'] = nested_data
            else:
                data['nested_links'] = []

            return data

        except Exception as e:
            return {'url': url, 'error': str(e), 'nested_links': []}