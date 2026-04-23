from mysql_helper import MysqlHelper  # 从同目录导入

class MovieRepository:
    def __init__(self, db: MysqlHelper):
        self.db = db

    def init_table(self):
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

    def save_movies(self, movies: list):
        self.db.execute("DELETE FROM douban_movies")
        success = 0
        for movie in movies:
            if self.db.insert("douban_movies", movie):
                success += 1
        print(f"存库完成！成功 {success}/{len(movies)}")

    def get_ratings(self):
        return [r[0] for r in self.db.query("SELECT rating FROM douban_movies") or []]

    def get_years(self):
        return [r[0] for r in self.db.query("SELECT year FROM douban_movies WHERE year > 0") or []]

    def get_genres(self):
        return [r[0] for r in self.db.query("SELECT genre FROM douban_movies WHERE genre != ''") or []]

    def get_countries(self):
        return [r[0] for r in self.db.query("SELECT country FROM douban_movies WHERE country != ''") or []]