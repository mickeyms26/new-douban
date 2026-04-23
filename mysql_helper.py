import pymysql

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