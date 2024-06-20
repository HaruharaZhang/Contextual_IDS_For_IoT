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

def create_database_and_tables(dbname, messages):
    db_config = get_db_config()
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
            username VARCHAR(255) NOT NULL UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS config_details (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(255) NOT NULL,
            name VARCHAR(255),
            zigbeechannel INT,
            mac VARCHAR(255),
            dhcp BOOLEAN,
            ipaddress VARCHAR(255),
            netmask VARCHAR(255),
            gateway VARCHAR(255),
            proxyaddress VARCHAR(255),
            proxyport INT,
            utc TIMESTAMP,
            `localtime` TIMESTAMP,
            timezone VARCHAR(255),
            swversion VARCHAR(255),
            apiversion VARCHAR(255),
            linkbutton BOOLEAN,
            portalservices BOOLEAN,
            portalconnection VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS lights (
        id INT AUTO_INCREMENT PRIMARY KEY,
        username VARCHAR(255),
        light_id VARCHAR(255),
        state JSON,
        swupdate JSON,
        type VARCHAR(255),
        name VARCHAR(255),
        modelid VARCHAR(255),
        manufacturername VARCHAR(255),
        productname VARCHAR(255),
        capabilities JSON,
        config JSON,
        uniqueid VARCHAR(255),
        swversion VARCHAR(255),
        swconfigid VARCHAR(255),
        productid VARCHAR(255),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS `groups` (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(255),
            group_id VARCHAR(255),
            name VARCHAR(255),
            lights JSON,
            sensors JSON,
            type VARCHAR(255),
            state JSON,
            recycle BOOLEAN,
            class VARCHAR(255),
            action JSON,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS schedules (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(255),
            schedule_id VARCHAR(255),
            name VARCHAR(255),
            description VARCHAR(255),
            command JSON,
            `localtime` VARCHAR(255),
            time VARCHAR(255),
            created TIMESTAMP,
            status VARCHAR(255),
            autodelete BOOLEAN,
            starttime TIMESTAMP,
            recycle BOOLEAN,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scenes (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(255),
            scene_id VARCHAR(255),
            name VARCHAR(255),
            type VARCHAR(255),
            lights JSON,
            owner VARCHAR(255),
            recycle BOOLEAN,
            locked BOOLEAN,
            appdata JSON,
            picture VARCHAR(255),
            image VARCHAR(255),
            lastupdated TIMESTAMP,
            version INT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS sensors (
        id INT AUTO_INCREMENT PRIMARY KEY,
        username VARCHAR(255),
        sensor_id VARCHAR(255),
        state JSON,
        swupdate JSON,
        config JSON,
        name VARCHAR(255),
        type VARCHAR(255),
        modelid VARCHAR(255),
        manufacturername VARCHAR(255),
        productname VARCHAR(255),
        diversityid VARCHAR(255),
        swversion VARCHAR(255),
        uniqueid VARCHAR(255),
        capabilities JSON,
        recycle BOOLEAN,
        battery INT,
        pending JSON,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS rules (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(255),
            rule_id VARCHAR(255),
            name VARCHAR(255),
            owner VARCHAR(255),
            created TIMESTAMP,
            lasttriggered VARCHAR(255),
            timestriggered INT,
            status VARCHAR(255),
            recycle BOOLEAN,
            conditions JSON,
            actions JSON,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()
    print(messages['database_created'])


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

# 获取配置并存储到数据库
def store_config_details(dbname, username, config_data, messages):
    conn = connect_db(dbname)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO config_details (
            username, name, zigbeechannel, mac, dhcp, ipaddress, netmask, gateway,
            proxyaddress, proxyport, utc, `localtime`, timezone, swversion, apiversion,
            linkbutton, portalservices, portalconnection
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE 
            name = VALUES(name), zigbeechannel = VALUES(zigbeechannel), mac = VALUES(mac),
            dhcp = VALUES(dhcp), ipaddress = VALUES(ipaddress), netmask = VALUES(netmask),
            gateway = VALUES(gateway), proxyaddress = VALUES(proxyaddress),
            proxyport = VALUES(proxyport), utc = VALUES(utc), `localtime` = VALUES(`localtime`),
            timezone = VALUES(timezone), swversion = VALUES(swversion), apiversion = VALUES(apiversion),
            linkbutton = VALUES(linkbutton), portalservices = VALUES(portalservices),
            portalconnection = VALUES(portalconnection)
    ''', (
        username, config_data.get('name'), config_data.get('zigbeechannel'), config_data.get('mac'),
        config_data.get('dhcp'), config_data.get('ipaddress'), config_data.get('netmask'),
        config_data.get('gateway'), config_data.get('proxyaddress'), config_data.get('proxyport'),
        config_data.get('UTC'), config_data.get('localtime'), config_data.get('timezone'),
        config_data.get('swversion'), config_data.get('apiversion'), config_data.get('linkbutton'),
        config_data.get('portalservices'), config_data.get('portalconnection')
    ))
    conn.commit()
    conn.close()
    print(messages['config_stored'])

# 从API获取配置
def get_config(ip, username):
    url = f"https://{ip}/api/{username}/config"
    response = requests.get(url, verify=False)
    if response.status_code == 200:
        return response.json()
    return None

# 检查是否存在用户名
def username_exists(dbname, username):
    conn = connect_db(dbname)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
    result = cursor.fetchone()
    conn.close()
    return result is not None

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
            print(messages['user_created'], response_json)
            username = response_json[0]['success'].get('username')
            if username:
                insert_username(dbname, ip, username, messages)
                config_data = get_config(ip, username)
                if config_data:
                    store_config_details(dbname, username, config_data, messages)
            break
        else:
            print(messages['create_user_failed'], response.status_code, response.text)
            break

# 比较配置数据
def compare_and_update_config(dbname, ip, username, new_config, messages):
    conn = connect_db(dbname)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM config_details WHERE username = %s', (username,))
    result = cursor.fetchone()
    if result:
        # 逐一比较每个字段
        for key, value in new_config.items():
            if key in result and result[key] != value:
                cursor.execute('''
                    UPDATE config_details SET {} = %s WHERE username = %s
                '''.format(f'`{key}`'), (value, username))
                conn.commit()
                print(f"{messages['config_updated']} {key}")
        print(messages['config_check_complete'])
    else:
        store_config_details(dbname, username, new_config, messages)
    conn.close()

def fetch_and_store_data(ip, username, endpoint, table_name, dbname, messages):
    url = f"https://{ip}/api/{username}/{endpoint}"
    response = requests.get(url, verify=False)
    if response.status_code == 200:
        data = response.json()
        if not data:
            print(messages[f'{endpoint}_no_data'])
            return
        conn = connect_db(dbname)
        cursor = conn.cursor()
        for item_id, item_data in data.items():
            try:
                if table_name == 'lights':
                    cursor.execute(f'''
                        INSERT INTO lights (username, light_id, state, swupdate, type, name, modelid, manufacturername, productname, capabilities, config, uniqueid, swversion, swconfigid, productid)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE state = VALUES(state), swupdate = VALUES(swupdate), type = VALUES(type), name = VALUES(name), modelid = VALUES(modelid),
                        manufacturername = VALUES(manufacturername), productname = VALUES(productname), capabilities = VALUES(capabilities), config = VALUES(config),
                        uniqueid = VALUES(uniqueid), swversion = VALUES(swversion), swconfigid = VALUES(swconfigid), productid = VALUES(productid)
                    ''', (username, item_id, json.dumps(item_data.get('state')), json.dumps(item_data.get('swupdate')), item_data.get('type'), item_data.get('name'), item_data.get('modelid'), 
                        item_data.get('manufacturername'), item_data.get('productname'), json.dumps(item_data.get('capabilities')), json.dumps(item_data.get('config')), item_data.get('uniqueid'), 
                        item_data.get('swversion'), item_data.get('swconfigid'), item_data.get('productid')))
                elif table_name == 'groups':
                    cursor.execute(f'''
                        INSERT INTO `groups` (username, group_id, name, lights, sensors, type, state, recycle, class, action)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE name = VALUES(name), lights = VALUES(lights), sensors = VALUES(sensors), type = VALUES(type), state = VALUES(state),
                        recycle = VALUES(recycle), class = VALUES(class), action = VALUES(action)
                    ''', (username, item_id, item_data.get('name'), json.dumps(item_data.get('lights')), json.dumps(item_data.get('sensors')), item_data.get('type'), json.dumps(item_data.get('state')), 
                          item_data.get('recycle'), item_data.get('class'), json.dumps(item_data.get('action'))))
                elif table_name == 'schedules':
                    cursor.execute(f'''
                        INSERT INTO schedules (username, schedule_id, name, description, command, `localtime`, time, created, status, autodelete, starttime, recycle)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE name = VALUES(name), description = VALUES(description), command = VALUES(command), `localtime` = VALUES(`localtime`),
                        time = VALUES(time), created = VALUES(created), status = VALUES(status), autodelete = VALUES(autodelete), starttime = VALUES(starttime), recycle = VALUES(recycle)
                    ''', (username, item_id, item_data.get('name'), item_data.get('description'), json.dumps(item_data.get('command')), item_data.get('localtime'), item_data.get('time'), 
                          item_data.get('created'), item_data.get('status'), item_data.get('autodelete'), item_data.get('starttime'), item_data.get('recycle')))
                elif table_name == 'scenes':
                    cursor.execute(f'''
                        INSERT INTO sensors (username, sensor_id, state, swupdate, config, name, type, modelid, manufacturername, productname, diversityid, swversion, uniqueid, capabilities, recycle, battery, pending)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE state = VALUES(state), swupdate = VALUES(swupdate), config = VALUES(config), name = VALUES(name), type = VALUES(type),
                        modelid = VALUES(modelid), manufacturername = VALUES(manufacturername), productname = VALUES(productname), diversityid = VALUES(diversityid),
                        swversion = VALUES(swversion), uniqueid = VALUES(uniqueid), capabilities = VALUES(capabilities), recycle = VALUES(recycle), battery = VALUES(battery), pending = VALUES(pending)
                    ''', (username, item_id, json.dumps(item_data.get('state')), json.dumps(item_data.get('swupdate')), json.dumps(item_data.get('config')), item_data.get('name'), 
                        item_data.get('type'), item_data.get('modelid'), item_data.get('manufacturername'), item_data.get('productname'), item_data.get('diversityid'), item_data.get('swversion'), 
                        item_data.get('uniqueid'), json.dumps(item_data.get('capabilities')), item_data.get('recycle'), item_data.get('battery'), json.dumps(item_data.get('pending'))))
                elif table_name == 'sensors':
                    cursor.execute(f'''
                        INSERT INTO sensors (username, sensor_id, state, swupdate, config, name, type, modelid, manufacturername, productname, diversityid, swversion, uniqueid, capabilities, recycle)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE state = VALUES(state), swupdate = VALUES(swupdate), config = VALUES(config), name = VALUES(name), type = VALUES(type),
                        modelid = VALUES(modelid), manufacturername = VALUES(manufacturername), productname = VALUES(productname), diversityid = VALUES(diversityid),
                        swversion = VALUES(swversion), uniqueid = VALUES(uniqueid), capabilities = VALUES(capabilities), recycle = VALUES(recycle)
                    ''', (username, item_id, json.dumps(item_data.get('state')), json.dumps(item_data.get('swupdate')), json.dumps(item_data.get('config')), item_data.get('name'), 
                          item_data.get('type'), item_data.get('modelid'), item_data.get('manufacturername'), item_data.get('productname'), item_data.get('diversityid'), item_data.get('swversion'), 
                          item_data.get('uniqueid'), json.dumps(item_data.get('capabilities')), item_data.get('recycle')))
                elif table_name == 'rules':
                    cursor.execute(f'''
                        INSERT INTO rules (username, rule_id, name, owner, created, lasttriggered, timestriggered, status, recycle, conditions, actions)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE name = VALUES(name), owner = VALUES(owner), created = VALUES(created), lasttriggered = VALUES(lasttriggered),
                        timestriggered = VALUES(timestriggered), status = VALUES(status), recycle = VALUES(recycle), conditions = VALUES(conditions), actions = VALUES(actions)
                    ''', (username, item_id, item_data.get('name'), item_data.get('owner'), item_data.get('created'), item_data.get('lasttriggered'), item_data.get('timestriggered'), 
                          item_data.get('status'), item_data.get('recycle'), json.dumps(item_data.get('conditions')), json.dumps(item_data.get('actions'))))
            except pymysql.MySQLError as e:
                print(f"Error inserting {endpoint[:-1]} {item_id}: {e}")
        conn.commit()
        conn.close()
        print(messages[f'{endpoint}_stored'])
    else:
        print(messages[f'{endpoint}_failed'], response.status_code, response.text)

def fetch_all_data(ip, username, dbname, messages):
    endpoints = ['lights', 'groups', 'schedules', 'scenes', 'sensors', 'rules']
    for endpoint in endpoints:
        fetch_and_store_data(ip, username, endpoint, endpoint, dbname, messages)

def get_data(device_ip, messages, dbname):
    """获取设备数据并创建用户"""
    print(messages['start_get_data'])
    ip = device_ip
    if not ip:
        raise ValueError(messages['no_ip_found'])
    
    # 检查是否已经存在用户名
    conn = connect_db(dbname)
    cursor = conn.cursor()
    cursor.execute('SELECT username FROM users WHERE ip = %s', (ip,))
    result = cursor.fetchone()
    conn.close()
    if result:
        username = result['username']
        print(messages['username_exists'])
        config_data = get_config(ip, username)
        if config_data:
            compare_and_update_config(dbname, ip, username, config_data, messages)
        fetch_all_data(ip, username, dbname, messages)
    else:
        create_hue_user(ip, messages, dbname)

if __name__ == "__main__":
    # 定义数据库名称
    dbname = 'philips_hue_bridge_db'
    
    # 获取语言和消息
    lang = os.environ.get("LANGUAGE", "en")
    messages = get_messages(lang)

    # 创建数据库和表格
    create_database_and_tables(dbname, messages)

    # 获取 DEVICE_IP 参数
    device_ip = os.getenv('DEVICE_IP')
    print(messages['retrieved_device_ip'], device_ip)
    get_data(device_ip, messages, dbname)
