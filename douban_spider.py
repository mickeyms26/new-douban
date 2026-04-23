import requests
import time
import re
from bs4 import BeautifulSoup

class DoubanSpider:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept-Language': 'zh-CN,zh;q=0.9',
             'Cookie': 'bid=7Wi_1Vj2ELw; ck=qW_e; dbcl2="207570830:o8Q2btgMMJU"; ll="118130"; __utma=30149280.1902301549.1776925788.1776925788; __utmb=30149280.1.10.1776925788; __utmc=30149280; __utmz=30149280.1776925788.1.1.utmcsr=aisearch.sogou.com|utmccn=(organic)|utmcmd=organic; push_doumail_num=0; push_noty_num=0',  # ← 加这一行
        }

    def fetch_page(self, start: int) -> list:
        url = f'https://movie.douban.com/top250?start={start}'
        try:
            resp = requests.get(url, headers=self.headers, timeout=10)
            resp.raise_for_status()
        except Exception as e:
            print(f"请求失败(start={start}): {e}")
            return []
        return self.parse(resp.text)

    def parse(self, html: str) -> list:
        movies = []
        soup = BeautifulSoup(html, 'html.parser')
        for item in soup.select('ol.grid_view li'):
            try:
                rank = item.select_one('.pic em').text.strip()
                title = item.select_one('.title').text.strip()
                rating_elem = item.select_one('.rating_num')
                rating = rating_elem.text.strip() if rating_elem else '0.0'

                info_text = item.select_one('.bd p').text
                lines = [l.strip() for l in info_text.split('\n') if l.strip()]
                year, country, genre = 0, '', ''
                if len(lines) >= 2:
                    parts = [p.strip() for p in lines[1].split('/')]
                    if len(parts) >= 1:
                        m = re.search(r'\d{4}', parts[0])
                        year = int(m.group()) if m else 0
                    if len(parts) >= 2:
                        country = parts[1]
                    if len(parts) >= 3:
                        genre = parts[2].split()[0]

                movies.append({
                    "rank_num": int(rank),
                    "title": title,
                    "year": year,
                    "country": country,
                    "genre": genre,
                    "rating": float(rating)
                })
            except Exception as e:
                print(f"解析失败，跳过: {e}")
        return movies

    def run(self) -> list:
        all_movies = []
        for start in range(0, 100, 25):
            page_movies = self.fetch_page(start)
            all_movies.extend(page_movies)
            print(f"第{start // 25 + 1}页完成，已获取 {len(all_movies)} 部")
            time.sleep(2)
        return all_movies