import pymysql
import requests
import time
import re
from bs4 import BeautifulSoup
import matplotlib.pyplot as plt
import matplotlib
from collections import Counter


# ========== 1. MysqlHelper：只管数据库 ==========
class MysqlHelper:
    def __init__(self, host='localhost', user='root', password='', database='', port=3306, charset='utf8mb4'):
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.port = port
        self.charset = charset
        self.conn = None
        self.cur = None

    def connect(self):
        try:
            self.conn = pymysql.connect(
                host=self.host, user=self.user, password=self.password,
                database=self.database, port=self.port, charset=self.charset
            )
            self.cur = self.conn.cursor()
        except Exception as e:
            print(f"数据库连接失败: {e}")

    def close(self):
        if self.cur:
            self.cur.close()
        if self.conn:
            self.conn.close()

    def query(self, sql, params=None):
        try:
            self.connect()
            self.cur.execute(sql, params)
            return self.cur.fetchall()
        except Exception as e:
            print(f"查询失败: {e}")
            return None
        finally:
            self.close()

    def execute(self, sql, params=None):
        row = 0
        try:
            self.connect()
            row = self.cur.execute(sql, params)
            self.conn.commit()
        except Exception as e:
            if self.conn:
                self.conn.rollback()
            print(f"执行失败: {e}")
        finally:
            self.close()
        return row

    def insert(self, table, data: dict):
        keys = ','.join(data.keys())
        placeholders = ','.join(['%s'] * len(data))
        sql = f"INSERT INTO {table} ({keys}) VALUES ({placeholders})"
        return self.execute(sql, tuple(data.values()))

    def select(self, table, fields='*', where=None, params=None):
        sql = f"SELECT {fields} FROM {table}"
        if where:
            sql += f" WHERE {where}"
        return self.query(sql, params)


# ========== 2. MovieRepository：只管电影表的增删查 ==========
# 把"业务相关的SQL"从MysqlHelper里分离出来
class MovieRepository:
    def __init__(self, db: MysqlHelper):
        self.db = db  # 依赖注入，接收一个MysqlHelper实例

    def init_table(self):
        """建表"""
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS douban_movies (
                id INT AUTO_INCREMENT PRIMARY KEY,
                rank_num INT COMMENT '排名',
                title VARCHAR(100) COMMENT '电影名',
                year INT COMMENT '上映年份',
                country VARCHAR(100) COMMENT '国家/地区',
                genre VARCHAR(100) COMMENT '类型',
                rating FLOAT COMMENT '评分'
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        print("表已就绪！")

    def clear(self):
        """清空表"""
        self.db.execute("DELETE FROM douban_movies")

    def save_movies(self, movies: list):
        """批量存入电影数据"""
        self.clear()
        success = 0
        for movie in movies:
            if self.db.insert("douban_movies", movie):
                success += 1
        print(f"存库完成！成功 {success}/{len(movies)}")

    def get_all(self):
        """取出全部数据供外部使用"""
        return self.db.query("SELECT rank_num, title, year, country, genre, rating FROM douban_movies")

    def get_ratings(self):
        return [r[0] for r in self.db.query("SELECT rating FROM douban_movies") or []]

    def get_years(self):
        return [r[0] for r in self.db.query("SELECT year FROM douban_movies WHERE year > 0") or []]

    def get_genres(self):
        return [r[0] for r in self.db.query("SELECT genre FROM douban_movies WHERE genre != ''") or []]

    def get_countries(self):
        return [r[0] for r in self.db.query("SELECT country FROM douban_movies WHERE country != ''") or []]


# ========== 3. DoubanSpider：只管爬虫 ==========
class DoubanSpider:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept-Language': 'zh-CN,zh;q=0.9',
        }

    def fetch_page(self, start: int) -> list:
        """爬取单页，返回该页电影列表"""
        url = f'https://movie.douban.com/top250?start={start}'
        try:
            resp = requests.get(url, headers=self.headers, timeout=10)
            resp.raise_for_status()
        except Exception as e:
            print(f"请求失败(start={start}): {e}")
            return []

        return self.parse(resp.text)

    def parse(self, html: str) -> list:
        """解析HTML，返回电影数据列表"""
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
        """爬取全部100部，返回完整列表"""
        all_movies = []
        for start in range(0, 100, 25):
            page_movies = self.fetch_page(start)
            all_movies.extend(page_movies)
            print(f"第{start // 25 + 1}页完成，已获取 {len(all_movies)} 部")
            time.sleep(2)
        return all_movies


# ========== 4. ChartDrawer：只管画图，从repo取数据，不依赖爬虫 ==========
class ChartDrawer:
    def __init__(self, repo: MovieRepository):
        self.repo = repo  # 依赖注入，只需要一个能提供数据的repo
        matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans']
        matplotlib.rcParams['axes.unicode_minus'] = False

    def draw(self, save_path='douban.png'):
        """画4张图，数据全部来自数据库，与爬虫完全无关"""
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        fig.suptitle('豆瓣 Top 100 数据分析', fontsize=18)

        self._draw_ratings(axes[0, 0])
        self._draw_decades(axes[0, 1])
        self._draw_genres(axes[1, 0])
        self._draw_countries(axes[1, 1])

        plt.tight_layout()
        plt.savefig(save_path)
        print(f"图表已保存为 {save_path}")
        plt.show()

    def _draw_ratings(self, ax):
        ratings = self.repo.get_ratings()
        ax.hist(ratings, bins=10, color='steelblue', edgecolor='white')
        ax.set_title('① 评分分布')
        ax.set_xlabel('评分')
        ax.set_ylabel('数量')

    def _draw_decades(self, ax):
        years = self.repo.get_years()
        decade = Counter((y // 10) * 10 for y in years)
        decades_sorted = sorted(decade.keys())
        ax.bar([f"{d}s" for d in decades_sorted],
               [decade[d] for d in decades_sorted], color='coral', edgecolor='white')
        ax.set_title('② 年代分布')
        ax.set_xlabel('年代')
        ax.set_ylabel('数量')

    def _draw_genres(self, ax):
        top10 = Counter(self.repo.get_genres()).most_common(10)
        ax.barh([k for k, _ in top10], [v for _, v in top10], color='mediumseagreen')
        ax.set_title('③ 类型 TOP10')
        ax.set_xlabel('数量')

    def _draw_countries(self, ax):
        cty = Counter(self.repo.get_countries())
        top_cty = {k: v for k, v in cty.items() if v >= 3}
        other = sum(v for v in cty.values() if v < 3)
        if other > 0:
            top_cty['其他'] = other
        ax.pie(top_cty.values(), labels=top_cty.keys(), autopct='%1.1f%%',
               colors=plt.cm.Pastel1.colors)
        ax.set_title('④ 国家/地区占比')


# ========== 主程序：只负责组装和调用 ==========
if __name__ == '__main__':
    # 组装依赖
    db = MysqlHelper(host="localhost", user="root", password="123456", database="test_db")
    repo = MovieRepository(db)
    spider = DoubanSpider()
    chart = ChartDrawer(repo)

    # --- 想重新爬就运行这3行，只想画图就注释掉这3行 ---
    print("=== 1. 初始化表 ===")
    repo.init_table()
    print("\n=== 2. 爬取数据 ===")
    movies = spider.run()
    print("\n=== 3. 存入数据库 ===")
    repo.save_movies(movies)

    # --- 画图永远只依赖数据库，与爬虫无关 ---
    print("\n=== 4. 生成图表 ===")
    chart.draw()

    print("\n🎉 全部完成！")