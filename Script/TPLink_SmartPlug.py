import socket
import os
import pymysql
from configparser import ConfigParser
from struct import pack
import json
from datetime import datetime

def encrypt(string):
    key = 171
    result = pack(">I", len(string))
    for i in string:
        a = key ^ ord(i)
        key = a
        result += bytes([a])
    return result

def decrypt(string):
    key = 171
    result = ""
    for i in string:
        a = key ^ i
        key = i
        result += chr(a)
    return result

def read_config():
    config = ConfigParser()
    config.read('Config/database.cfg')
    return {
        'host': config.get('Database', 'host'),
        'port': config.getint('Database', 'port'),
        'user': config.get('Database', 'user'),
        'password': config.get('Database', 'password'),
        'database': 'tp_link_devices'
    }

def create_database_and_tables(db_config):
    connection = pymysql.connect(host=db_config['host'],
                                 user=db_config['user'],
                                 password=db_config['password'],
                                 port=db_config['port'])
    cursor = connection.cursor()
    cursor.execute("CREATE DATABASE IF NOT EXISTS tp_link_devices;")
    cursor.execute("USE tp_link_devices;")
    create_table_queries = [
        """
        CREATE TABLE IF NOT EXISTS device_info (
            device_id VARCHAR(255) NOT NULL,
            model VARCHAR(100),
            sw_ver VARCHAR(50),
            hw_ver VARCHAR(50),
            rssi INT,
            longitude_i INT,
            latitude_i INT,
            alias VARCHAR(100),
            status VARCHAR(50),
            mic_type VARCHAR(100),
            feature VARCHAR(50),
            mac VARCHAR(100),
            updating BOOLEAN,
            led_off BOOLEAN,
            child_num INT,
            ntc_state INT,
            err_code INT,
            PRIMARY KEY (device_id)
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS device_states (
            id INT AUTO_INCREMENT PRIMARY KEY,
            device_name VARCHAR(255), 
            device_id VARCHAR(255) NOT NULL,
            state TEXT,
            reachable BOOLEAN,
            api_url VARCHAR(255),
            last_updated DATETIME
        );
        """
    ]
    for query in create_table_queries:
        cursor.execute(query)
    connection.commit()
    cursor.close()
    connection.close()

def prepare_and_insert_device_state(db_config, device_info, is_child):
    api_url_suffix = "-children" if is_child else "-main"
    device_id = device_info.get('id' if is_child else 'deviceId', 'default_id')
    device_name = device_info.get('alias')
    state_json = json.dumps(device_info)
    reachable = 1 if device_info.get('err_code', 1) == 0 else 0
    device_ip = os.getenv("DEVICE_IP")
    api_url = f"Connector/TPLink_SmartPlug.py {api_url_suffix} {device_ip}"
    last_updated = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    connection = pymysql.connect(host=db_config['host'],
                                 user=db_config['user'],
                                 password=db_config['password'],
                                 port=db_config['port'],
                                 database=db_config['database'],
                                 cursorclass=pymysql.cursors.DictCursor)
    cursor = connection.cursor()
    insert_query = """
    INSERT INTO device_states (device_id, device_name, state, reachable, api_url, last_updated)
    VALUES (%s, %s, %s, %s, %s, %s);
    """
    cursor.execute(insert_query, (device_id, device_name, state_json, reachable, api_url, last_updated))
    connection.commit()
    cursor.close()
    connection.close()

# 清空指定数据库中的表格，但不删除表格本身。
def clear_table(db_config):
    connection = pymysql.connect(host=db_config['host'],
                                 user=db_config['user'],
                                 password=db_config['password'],
                                 port=db_config['port'],
                                 database=db_config['database'])  # 直接在连接中指定数据库
    cursor = connection.cursor()
    try:
        cursor.execute("DELETE FROM device_info;")
        cursor.execute("DELETE FROM device_states;")
        connection.commit()  # 确保提交更改
    except pymysql.MySQLError as e:
        print(f"Error clearing table tp_link_devices: {e}")
    finally:
        cursor.close()
        connection.close()  # 确保关闭连接


def main():
    ip = os.environ["DEVICE_IP"]
    port = 9999
    cmd = '{"system":{"get_sysinfo":{}}}'
    
    try:
        sock_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock_tcp.settimeout(10)
        sock_tcp.connect((ip, port))
        sock_tcp.send(encrypt(cmd))
        data = sock_tcp.recv(2048)
        sock_tcp.close()
        
        decrypted = decrypt(data[4:])
        device_info = json.loads(decrypted)['system']['get_sysinfo']
        db_config = read_config()
        create_database_and_tables(db_config)
        clear_table(db_config)
        prepare_and_insert_device_state(db_config, device_info, is_child=False)
        if 'children' in device_info:
            for child in device_info['children']:
                prepare_and_insert_device_state(db_config, child, is_child=True)


    except socket.error as e:
        print(f"Could not connect to host {ip}:{port}. Error: {str(e)}")
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == '__main__':
    main()
