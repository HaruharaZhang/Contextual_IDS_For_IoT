import requests
import json
import time
import urllib3
import os
import pymysql
from configparser import ConfigParser
from messageLoader import get_messages

# 忽略不安全请求警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

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

# 连接数据库
def connect_db(dbname):
    db_config = get_db_config()
    print(f"Debug: Connecting to DB with config: {db_config}")  # 添加调试信息
    conn = pymysql.connect(
        host=db_config['host'],
        port=db_config['port'],
        user=db_config['user'],
        password=db_config['password'],
        db=dbname,
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )
    return conn

# 创建数据库和表格
def create_database_and_tables(dbname):
    db_config = get_db_config()
    print(f"Debug: Creating database and tables with config: {db_config}")  # 添加调试信息
    conn = pymysql.connect(
        host=db_config['host'],
        port=db_config['port'],
        user=db_config['user'],
        password=db_config['password'],
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )
    cursor = conn.cursor()
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {dbname}")
    conn.select_db(dbname)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            ip VARCHAR(255) NOT NULL,
            username VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

# 插入用户名
def insert_username(dbname, ip, username, messages):
    conn = connect_db(dbname)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO users (ip, username)
        VALUES (%s, %s)
    ''', (ip, username))
    conn.commit()
    print(messages['insert_success'])  # 添加成功插入后的提示信息
    conn.close()

# 创建 Philips Hue 用户
def create_hue_user(ip, messages, dbname):
    """创建 Philips Hue 用户"""
    url = f"https://{ip}/api"
    body = {
        "devicetype": "my_hue_app#samsung_A32"
    }
    headers = {
        "Content-Type": "application/json"
    }

    while True:
        # 跳过证书验证发送 POST 请求
        response = requests.post(url, headers=headers, data=json.dumps(body), verify=False)
        response_json = response.json()

        if response.status_code == 200 and "error" in response_json[0]:
            error = response_json[0]["error"]
            if error["type"] == 101 and "link button not pressed" in error["description"]:
                print(messages['press_button'])
                time.sleep(1)
            else:
                print("出现其他错误:", error["description"])
                break
        elif response.status_code == 200:
            print("User created successfully:", response_json)
            username = response_json[0]['success'].get('username')
            if username:
                insert_username(dbname, ip, username, messages)
            break
        else:
            print("Failed to create user:", response.status_code, response.text)
            break

def get_data(device_ip, messages, dbname):
    """获取设备数据并创建用户"""
    print(f"Debug: get_data called with device_ip = {device_ip}")  # 添加调试信息
    ip = device_ip
    if not ip:
        raise ValueError("No IP address found in environment variables.")
    create_hue_user(ip, messages, dbname)

if __name__ == "__main__":
    # 定义数据库名称
    dbname = 'philips_hue_bridge_db'
    
    # 创建数据库和表格
    create_database_and_tables(dbname)

    # 获取 DEVICE_IP 参数
    device_ip = os.getenv('DEVICE_IP')
    lang = os.environ.get("LANGUAGE", "en")
    messages = get_messages(lang)
    print(f"Debug: Retrieved DEVICE_IP = {device_ip}")  # 添加调试信息
    get_data(device_ip, messages, dbname)
