import socket
import os
import pymysql
from configparser import ConfigParser
from struct import pack
import json
from datetime import datetime
import time

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

def load_config():
    config_path = os.path.join(os.path.dirname(__file__), '..', 'Config', 'Script', 'TPLink_PTE.cfg')
    config = ConfigParser()
    config.read(config_path, encoding='utf-8')  # 显式指定编码

    scan_config = {
            'database': config['Settings']['database_name'],
            'scan_interval': config['Settings']['scan_interval']
        }
    
    return scan_config

def read_config():
    # config = ConfigParser()
    # config.read('Config/database.cfg')
    # return {
    #     'host': config.get('Database', 'host'),
    #     'port': config.getint('Database', 'port'),
    #     'user': config.get('Database', 'user'),
    #     'password': config.get('Database', 'password'),
    #     'database': 'tp_link_devices'
    # }
     # 定义配置文件路径
    config_path = os.path.join(os.path.dirname(__file__), '..', 'Config', 'database.cfg')

    # 创建配置解析器并读取配置文件
    config = ConfigParser()
    read_files = config.read(config_path, encoding='utf-8')  # 显式指定编码
    if not read_files:
        print("Failed to read any configuration files, please check the path and encoding.")
        return None


    database = load_config()
    # 尝试获取数据库配置
    try:
        db_config = {
            'host': config['Database']['host'],
            'port': int(config['Database']['port']),
            'user': config['Database']['user'],
            'password': config['Database']['password'],
            'database': database['database']
        }
    except KeyError as e:
        print("Key error:", e, "Check your configuration file sections and keys.")
        return None
    except Exception as e:
        print("An error occurred while parsing the database configuration:", str(e))
        return None

    return db_config

def create_database_and_tables(db_config):
    connection = pymysql.connect(host=db_config['host'],
                                 user=db_config['user'],
                                 password=db_config['password'],
                                 port=db_config['port'])
    cursor = connection.cursor()
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_config['database']};")
    cursor.execute(f"USE {db_config['database']};")
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

def prepare_and_insert_device_state(ip, db_config, device_info):
    device_id = device_info.get('deviceId')
    device_name = device_info.get('alias')
    state_json = json.dumps(device_info)
    reachable = 1 if device_info.get('err_code', 1) == 0 else 0
    device_ip = ip
    api_url = f"Connector/TPLink_PTE.py {device_ip}"
    last_updated = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    call_procedure(db_config, device_name, device_id, state_json, reachable, api_url, last_updated)

    # connection = pymysql.connect(host=db_config['host'],
    #                              user=db_config['user'],
    #                              password=db_config['password'],
    #                              port=db_config['port'],
    #                              database=db_config['database'],
    #                              cursorclass=pymysql.cursors.DictCursor)
    # cursor = connection.cursor()
    # insert_query = """
    # INSERT INTO device_states (device_id, device_name, state, reachable, api_url, last_updated)
    # VALUES (%s, %s, %s, %s, %s, %s)
    # ON DUPLICATE KEY UPDATE device_name = VALUES(device_name), state = VALUES(state), reachable = VALUES(reachable), api_url = VALUES(api_url), last_updated = VALUES(last_updated);
    # """
    # cursor.execute(insert_query, (device_id, device_name, state_json, reachable, api_url, last_updated))
    # connection.commit()
    # cursor.close()
    # connection.close()

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

# 创建一个数据库事务，将设备状态写入数据库。
def create_procedure(db_config):
    try:
        connection = pymysql.connect(host=db_config['host'],
                                 user=db_config['user'],
                                 password=db_config['password'],
                                 port=db_config['port'],
                                 database=db_config['database'])  # 直接在连接中指定数据库
        cursor = connection.cursor()

        # 首先删除已存在的存储过程
        cursor.execute('DROP PROCEDURE IF EXISTS ManageDeviceState;')

        # 定义存储过程
        procedure = """
        CREATE PROCEDURE ManageDeviceState(
            IN p_device_id VARCHAR(255),
            IN p_device_name VARCHAR(255),
            IN p_state JSON,
            IN p_reachable BOOLEAN,
            IN p_api_url VARCHAR(255),
            IN p_last_updated TIMESTAMP
        )
        BEGIN
            DECLARE v_device_id VARCHAR(255);

            START TRANSACTION;

            -- 尝试根据 device_name 查找记录
            SELECT device_id INTO v_device_id FROM device_states 
            WHERE device_name = p_device_name FOR UPDATE;

            -- 根据上一条语句的结果决定是插入还是更新
            IF v_device_id IS NOT NULL THEN
                -- 更新已存在的记录
                UPDATE device_states
                SET state = p_state, reachable = p_reachable, api_url = p_api_url, last_updated = p_last_updated
                WHERE device_name = p_device_name;
            ELSE
                -- 插入新记录
                INSERT INTO device_states (device_id, device_name, state, reachable, api_url, last_updated)
                VALUES (p_device_id, p_device_name, p_state, p_reachable, p_api_url, p_last_updated);
            END IF;

            COMMIT;
        END;
        """
        
        # 执行SQL语句创建存储过程
        cursor.execute(procedure)
        connection.commit()
    except pymysql.MySQLError as e:
        print("Error while connecting to MySQL", e)
    finally:
        cursor.close()
        connection.close()

def call_procedure(db_config, device_name, device_id, state, reachable, api_url, last_updated):

    try:
        connection = pymysql.connect(host=db_config['host'],
                                 user=db_config['user'],
                                 password=db_config['password'],
                                 port=db_config['port'],
                                 database=db_config['database'])  # 直接在连接中指定数据库
        cursor = connection.cursor()
        # 调用存储过程
        args = (device_name, device_id, state, reachable, api_url, last_updated)
        cursor.callproc('ManageDeviceState', args)
        connection.commit()
    except pymysql.MySQLError as e:
        print("Error while connecting to MySQL", e)
    finally:
        # 关闭数据库连接
        cursor.close()
        connection.close()

# 设置一个循环，这个循环会不停运行，然后休眠指定时间。循环会不停从设备获取状态，然后将状态写入数据库。
def get_device_state_loop(ip, port, db_config):
    scan_config = load_config()
    sysinfo_cmd = '{"system":{"get_sysinfo":{}}}'
    emeter_cmd = '{"emeter":{"get_realtime":{}}}' # 获取实时电量
    while True:
        try:
            sock_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock_tcp.settimeout(10)
            sock_tcp.connect((ip, port))
            sock_tcp.send(encrypt(sysinfo_cmd))
            data = sock_tcp.recv(2048)
            sock_tcp.close()
            decrypted = decrypt(data[4:])
            sysinfo_device_info = json.loads(decrypted)['system']['get_sysinfo']

            
            sock_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock_tcp.settimeout(10)
            sock_tcp.connect((ip, port))
            sock_tcp.send(encrypt(emeter_cmd))
            data = sock_tcp.recv(2048)
            sock_tcp.close()
            decrypted = decrypt(data[4:])
            emeter_device_info = json.loads(decrypted)['emeter']['get_realtime']
            device_info = {**sysinfo_device_info, **emeter_device_info}
            prepare_and_insert_device_state(ip, db_config, device_info)
    
        except socket.error as e:
            print(f"Could not connect to host {ip}:{port}. Error: {str(e)}")
        except Exception as e:
            print(f"An error occurred: {str(e)}")
        time.sleep(float(scan_config['scan_interval']))

def main():
    ip = os.environ["DEVICE_IP"]
    #ip = "192.168.88.223"
    port = 9999
    db_config = read_config()
    create_database_and_tables(db_config)
    clear_table(db_config)
    create_procedure(db_config)
    get_device_state_loop(ip, port, db_config)
    

if __name__ == '__main__':
    main()
