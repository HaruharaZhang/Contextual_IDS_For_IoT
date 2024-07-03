import configparser
import time
import datetime
import os
import requests
import pymysql
import subprocess
import json
from termcolor import colored
from datetime import datetime, timedelta


from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

def load_config():
    config = configparser.ConfigParser()
    config.read(['Config/Model/lightControl.cfg', 'Config/database.cfg'])
    settings = config['Settings']
    database = config['Database']
    
    return (float(settings['scan_interval']), float(settings['timeout']), 
            database['user'], database['password'], database['host'], settings['database'])



def fetch_device_states(conn, db_name):
    conn.select_db(db_name)
    with conn.cursor(pymysql.cursors.DictCursor) as cursor:
        cursor.execute("SELECT * FROM device_states;")
        devices = cursor.fetchall()
    return devices

def fetch_button_last_updated(conn, db_name):
    # 连接到特定的数据库
    conn.select_db(db_name)
    with conn.cursor(pymysql.cursors.DictCursor) as cursor:
        # 查询特定的按钮事件传感器，假设type='ZLLSwitch'用于识别按钮
        cursor.execute("SELECT state FROM sensors WHERE type='ZLLSwitch';")
        result = cursor.fetchone()
        if result:
            # 解析 state 字段中的 lastupdated 时间
            state = eval(result['state'])
            last_updated = state.get('lastupdated', 'none')
            if last_updated != 'none':
                last_updated = datetime.strptime(last_updated, '%Y-%m-%dT%H:%M:%S')
                #print(last_updated)
                return last_updated
    return None

# True -> 事件为最近发生的
# False -> 事件发生时间大于阈值
def is_recent_event():
    scan_interval, timeout, db_user, db_password, db_host, db_name = load_config()
    conn = pymysql.connect(user=db_user, password=db_password, host=db_host)
    last_updated = fetch_button_last_updated(conn, db_name)
    if last_updated:
        current_time = datetime.now().replace(microsecond=0)
        print(current_time, last_updated)
        print(last_updated + timedelta(seconds=scan_interval + 0.2))
        print(current_time <= last_updated + timedelta(seconds=scan_interval + 0.2))
        # 检查时间间隔是否在允许的范围内
        if current_time <= last_updated + timedelta(seconds=scan_interval + 0.2):
            return True
    return False

def update_database(data):
    print("inside update database function!")
    scan_interval, timeout, db_user, db_password, db_host, db_name= load_config()
    conn = pymysql.connect(user=db_user, password=db_password, host=db_host)
    cursor = conn.cursor()
    sql = """
        INSERT INTO sensors (state, swupdate, config, name, type, modelid, manufacturername, productname, diversityid, swversion, uniqueid, capabilities)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE 
        state = VALUES(state), 
        swupdate = VALUES(swupdate), 
        config = VALUES(config), 
        name = VALUES(name), 
        type = VALUES(type),
        modelid = VALUES(modelid), 
        manufacturername = VALUES(manufacturername), 
        productname = VALUES(productname), 
        diversityid = VALUES(diversityid), 
        swversion = VALUES(swversion), 
        uniqueid = VALUES(uniqueid), 
        capabilities = VALUES(capabilities)
    """
    values = (
        json.dumps(data.get('state', {})),
        json.dumps(data.get('swupdate', {})),
        json.dumps(data.get('config', {})),
        data.get('name', 'Unknown Name'),
        data.get('type', 'Unknown Type'),
        data.get('modelid', 'Unknown Model'),
        data.get('manufacturername', 'Unknown Manufacturer'),
        data.get('productname', 'Unknown Product'),
        data.get('diversityid'), 
        data.get('swversion', 'Unknown SW Version'),
        data.get('uniqueid'),
        json.dumps(data.get('capabilities', {})),
    )
    try:
        cursor.execute(sql, values)
        conn.commit()
        print("databae updated")
    except Exception as e:
        print(f"Database error: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

    
def check_devices(devices, timeout):
    for device in devices:
        try:
            response = requests.get(device['api_url'], verify=False, timeout=timeout)
            data = response.json()

            # 获取状态
            current_state = data.get('state', {}).get('on')
            current_bright = data.get('state', {}).get('bri')

            # 获取设备名称
            device_name = device['device_name']

            # 转换数据库中的状态
            db_state = json.loads(device['state'])
            db_light_state = db_state['state']['on']
            db_brightness = db_state['state']['bri']
            
            if db_light_state != current_state:
                if is_recent_event():
                    update_database(data)
                    return
                else:
                    warning_msg = f"[Alert][{datetime.now()}] Device '{device_name}' state changed! Database state: {db_light_state}, Current state: {current_state}"
                    print(colored(warning_msg, 'red'))
            if(current_state):
                if db_brightness != current_bright:
                    if is_recent_event():
                        update_database(data)
                        return
                    else:
                        warning_msg = f"[Alert][{datetime.now()}] Device '{device_name}' bright changed! Database bright: {db_brightness}, Current bright: {current_bright}"
                        print(colored(warning_msg, 'red'))

        except requests.RequestException as e:
            print(colored(f"Error accessing {device['api_url']}: {e}", 'yellow'))
        except ValueError as e:
            print(colored(f"Error parsing JSON from {device['api_url']}: {e}", 'yellow'))
    return

def main():
    scan_interval, timeout, db_user, db_password, db_host, db_name= load_config()
    conn = pymysql.connect(user=db_user, password=db_password, host=db_host)

    try:
        while True:
            devices = fetch_device_states(conn, db_name)
            check_devices(devices, timeout)
            time.sleep(scan_interval)
    finally:
        conn.close()

if __name__ == "__main__":
    main()

