import json
import requests
from bs4 import BeautifulSoup


class SyncParser:
    def __init__(self, url):
        self.url = url
        self.soup = self._get_html()

    def _get_html(self) -> BeautifulSoup:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 '
                          '(KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
        }
        response = requests.get(self.url, headers=headers)
        soup = BeautifulSoup(response.text, 'lxml')
        return soup

    def get_articles(self) -> list:
        articles_div = self.soup.find(name='div', class_='tm-articles-list')
        articles = articles_div.find_all(name='article', class_='tm-articles-list__item')
        return articles

    def get_pages_count(self) -> int:
        pagination_pages = self.soup.find(name='div', class_='tm-pagination__pages')
        last_page = pagination_pages.find_all(name='a', class_='tm-pagination__page')[-1].text
        return int(last_page)

    def get_all_articles(self):
        all_articles = []
        for page in range(1, self.get_pages_count() + 1):
            self.url = f'{self.url}page{page}'
            all_articles.extend(self.get_articles())
        return all_articles

    def get_formated_posts(self):
        posts_list = []
        for page, article in enumerate(self.get_all_articles(), start=1):
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

    def write_to_json(self):
        with open('posts.json', 'w') as file:
            json.dump(self.get_formated_posts(), file, ensure_ascii=False, indent=4)

    def write_to_csv(self):
        with open('posts.csv', 'w') as file:
            file.write(f'id;title;image_link;body;link\n')
            for post in self.get_formated_posts():
                file.write(f'{post["id"]};{post["title"]};{post["image_link"]};{post["body"]};{post["link"]}\n')


base_url = 'https://habr.com/ru/flows/develop/articles/'

parser = SyncParser(url=base_url)
parser.write_to_json()
parser.write_to_csv()
