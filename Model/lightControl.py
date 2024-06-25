import configparser
import time
import datetime
import os
import requests
import pymysql
import subprocess
import json
from termcolor import colored


from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# philips_hue_bridge_db -> philips_hue_bridge 的每秒扫描间隔

def load_config():
    config = configparser.ConfigParser()
    config.read('Config/Model/lightControl.cfg')
    timeout = float(config['Settings']['timeout'])
    db_name = config['Settings']['database']
    scan_interval = float(config['Settings']['scan_interval'])
    
    config.read('Config/database.cfg')
    db_user = config['Database']['user']
    db_password = config['Database']['password']
    db_host = config['Database']['host']
    
    return scan_interval, timeout, db_user, db_password, db_host, db_name

def fetch_device_states(conn, db_name):
    conn.select_db(db_name)
    with conn.cursor(pymysql.cursors.DictCursor) as cursor:
        cursor.execute("SELECT * FROM device_states;")
        devices = cursor.fetchall()
    return devices

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
                warning_msg = f"[Alert][{datetime.datetime.now()}] Device '{device_name}' state changed! Database state: {db_light_state}, Current state: {current_state}"
                print(colored(warning_msg, 'red'))
            if db_brightness != current_bright:
                warning_msg = f"[Alert][{datetime.datetime.now()}] Device '{device_name}' bright changed! Database state: {db_brightness}, Current state: {current_bright}"
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

