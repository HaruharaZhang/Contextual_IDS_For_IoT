import pymysql
from configparser import ConfigParser
import os

# 从配置文件读取数据库信息
def get_db_config():
    config = ConfigParser()
    config.read(os.path.join('config', 'database.cfg'))
    db_config = {
        'host': config['Database']['host'],
        'port': int(config['Database']['port']),
        'user': config['Database']['user'],
        'password': config['Database']['password']
    }
    return db_config

# 连接数据库并测试连接
def test_db_connection():
    db_config = get_db_config()
    print(f"Debug: Connecting to DB with config: {db_config}")  # 添加调试信息
    try:
        conn = pymysql.connect(
            host=db_config['host'],
            port=db_config['port'],
            user=db_config['user'],
            password=db_config['password'],
            db='test_db',  # 使用系统数据库进行连接测试
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        print("Connection to the database was successful!")
        conn.close()
    except pymysql.MySQLError as e:
        print(f"Error connecting to the database: {e}")

if __name__ == "__main__":
    test_db_connection()
