import configparser
import time
import requests
import pymysql

from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

def load_config():
    config = configparser.ConfigParser()
    config.read('Config/Model/keepAlive.cfg')
    scan_interval = float(config['Settings']['scan_interval'])
    
    config.read('Config/database.cfg')
    db_user = config['Database']['user']
    db_password = config['Database']['password']
    db_host = config['Database']['host']
    exclude_databases = [db.strip() for db in config['Database']['exclude_databases'].split(',')]
    
    return scan_interval, db_user, db_password, db_host, exclude_databases

def get_databases(conn, exclude_databases):
    with conn.cursor() as cursor:
        cursor.execute("SHOW DATABASES;")
        databases = [db[0] for db in cursor.fetchall() if db[0].strip() not in exclude_databases]
    return databases

def fetch_device_states(conn, db_name):
    conn.select_db(db_name)
    with conn.cursor(pymysql.cursors.DictCursor) as cursor:
        cursor.execute("SELECT api_url, reachable FROM device_states;")
        devices = cursor.fetchall()
    return devices

from termcolor import colored

def check_devices(devices):
    state_changes = []
    for device in devices:
        try:
            response = requests.get(device['api_url'], verify=False)
            data = response.json()
            # 获取 'reachable' 状态
            current_reachable = data.get('state', {}).get('reachable')
            # 获取设备名称
            device_name = data.get('name', 'Unknown Device')

            # 转换数据库中的状态
            db_reachable = bool(device['reachable'])

            if db_reachable != current_reachable:
                warning_msg = f"Alert: Device '{device_name}' state changed! Database state: {db_reachable}, Current state: {current_reachable}"
                print(colored(warning_msg, 'red'))
                state_changes.append({
                    'api_url': device['api_url'],
                    'device_name': device_name,
                    'database_state': db_reachable,
                    'current_state': current_reachable
                })

        except requests.RequestException as e:
            print(colored(f"Error accessing {device['api_url']}: {e}", 'yellow'))
        except ValueError as e:
            print(colored(f"Error parsing JSON from {device['api_url']}: {e}", 'yellow'))
    return state_changes


def main():
    scan_interval, db_user, db_password, db_host, exclude_databases = load_config()
    conn = pymysql.connect(user=db_user, password=db_password, host=db_host)

    try:
        databases = get_databases(conn, exclude_databases)
        while True:
            for db_name in databases:
                devices = fetch_device_states(conn, db_name)
                check_devices(devices)
            time.sleep(scan_interval)
    finally:
        conn.close()

if __name__ == "__main__":
    main()

