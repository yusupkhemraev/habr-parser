import json
import asyncio
from typing import Optional, List

import aiohttp
from bs4 import BeautifulSoup


class AsyncParser:

    def __init__(self, url: str):
        self.url = url

    @staticmethod
    async def make_request(url: str):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) '
                          'Version/17.3.1 Safari/605.1.15',
            'Accept': 'application/json, text/plain, */*'
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    response.raise_for_status()
                    return await response.text()
        except (aiohttp.ClientConnectorError, aiohttp.ServerDisconnectedError, aiohttp.ClientResponseError) as ex:
            print(f"Request error: {ex}")
            return None

    async def get_soup(self):
        html = await self.make_request(url=self.url)
        if html is None:
            return None
        return BeautifulSoup(html, 'lxml')

    async def get_pages_count(self):
        soup = await self.get_soup()
        if soup is None:
            return 0
        pagination_pages = soup.find(name='div', class_='tm-pagination__pages')
        if pagination_pages is None:
            return 1
        last_page = pagination_pages.find_all(name='a', class_='tm-pagination__page')[-1].text
        return int(last_page)

    async def get_all_html_pages(self):
        pages_count = await self.get_pages_count()
        if pages_count == 0:
            return []
        html_pages = await asyncio.gather(
            *[
                self.make_request(url=f'{self.url}page{page}')
                for page in range(1, pages_count + 1)
            ]
        )
        return html_pages

    def parse_html(self, html_page: str):
        return BeautifulSoup(html_page, 'lxml')

    async def get_all_pages_soup(self):
        html_pages = await self.get_all_html_pages()
        return [
            self.parse_html(html_page)
            for html_page in html_pages if html_page
        ]

    def get_posts(self, page_soup: BeautifulSoup):
        articles_div = page_soup.find(name='div', class_='tm-articles-list')
        articles = articles_div.find_all(name='article', class_='tm-articles-list__item')
        return articles

    async def get_formated_posts(self):
        pages_soup = await self.get_all_pages_soup()

        posts_list = []
        for page, article in enumerate(pages_soup, start=1):
            img = article.find(name='img', class_='tm-article-snippet__lead-image')
            title_tag = article.find(name='a', class_='tm-title__link')
            posts_list.append(
                dict(
                    id=page,
                    title=title_tag.text.strip(),
                    image_link=img.get('src') if img else None,
                    body=article.find(name='div', class_='article-formatted-body').text.strip(),
                    link='https://habr.com' + title_tag.get('href')
                )
            )
        return posts_list

    async def write_to_json(self):
        with open('posts.json', 'w') as file:
            json.dump(await self.get_formated_posts(), file, ensure_ascii=False, indent=4)

    async def write_to_csv(self):
        formated_posts = await self.get_formated_posts()
        with open('posts.csv', 'w') as file:
            file.write(f'id;title;image_link;body;link\n')
            for post in formated_posts:
                file.write(f'{post["id"]};{post["title"]};{post["image_link"]};{post["body"]};{post["link"]}\n')


async def main():
    parser = AsyncParser(url='https://habr.com/ru/flows/develop/articles/')
    await parser.write_to_json()
    await parser.write_to_csv()


if __name__ == '__main__':
    asyncio.run(main())

