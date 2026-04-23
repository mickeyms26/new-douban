from mysql_helper import MysqlHelper
from movie_repository import MovieRepository
from douban_spider import DoubanSpider
from chart_drawer import ChartDrawer

if __name__ == '__main__':
    # 组装
    db = MysqlHelper(host="localhost", user="root", password="123456", database="test_db")
    repo = MovieRepository(db)
    spider = DoubanSpider()
    chart = ChartDrawer(repo)

    # 建表
    print("=== 1. 初始化表 ===")
    repo.init_table()

    # 爬虫 + 存库（不想重爬就注释掉这5行）
    print("\n=== 2. 爬取数据 ===")
    movies = spider.run()
    print("\n=== 3. 存入数据库 ===")
    repo.save_movies(movies)

    # 画图（永远可以单独跑）
    print("\n=== 4. 生成图表 ===")
    chart.draw()

    print("\n🎉 全部完成！")