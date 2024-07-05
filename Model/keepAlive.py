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
    
    
    # 读取 keepAlive.cfg 配置文件
    keep_alive_path = os.path.join(os.path.dirname(__file__), '..', 'Config', 'Model', 'keepAlive.cfg')
    config = configparser.ConfigParser()
    read_files = config.read(keep_alive_path, encoding='utf-8')  # 显式指定编码

    if not read_files:
        print("Failed to read keepAlive configuration file, please check the path and encoding.")
        return None
    
    try:
        philips_hue_bridge_db = float(config['Settings']['philips_hue_bridge_db'])
        timeout = float(config['Settings']['timeout'])
    except KeyError as e:
        print("Key error:", e, "Check your keepAlive configuration file sections and keys.")
        return None
    except Exception as e:
        print("An error occurred while parsing the keepAlive configuration:", str(e))
        return None
    
    # 读取 database.cfg 配置文件
    database_path = os.path.join(os.path.dirname(__file__), '..', 'Config', 'database.cfg')
    read_files = config.read(database_path, encoding='utf-8')  # 显式指定编码
    if not read_files:
        print("Failed to read database configuration file, please check the path and encoding.")
        return None
    
    try:
        db_user = config['Database']['user']
        db_password = config['Database']['password']
        db_host = config['Database']['host']
        exclude_databases = [db.strip() for db in config['Database']['exclude_databases'].split(',')]
    except KeyError as e:
        print("Key error:", e, "Check your database configuration file sections and keys.")
        return None
    except Exception as e:
        print("An error occurred while parsing the database configuration:", str(e))
        return None

    return {
        'philips_hue_bridge_db': philips_hue_bridge_db,
        'timeout': timeout,
        'db_user': db_user,
        'db_password': db_password,
        'db_host': db_host,
        'exclude_databases': exclude_databases
    }

def get_databases(conn, exclude_databases):
    with conn.cursor() as cursor:
        cursor.execute("SHOW DATABASES;")
        databases = [db[0] for db in cursor.fetchall() if db[0].strip() not in exclude_databases]
    #print(f"Available databases: {databases}")
    return databases

def fetch_device_states(conn, db_name):
    conn.select_db(db_name)
    with conn.cursor(pymysql.cursors.DictCursor) as cursor:
        cursor.execute("SELECT api_url, reachable, device_name FROM device_states;")
        devices = cursor.fetchall()
    return devices

def check_devices(devices, timeout):
    state_changes = []
    for device in devices:
        if device['api_url'].startswith('Connector'):
            # Assume the script and parameters are correctly formatted in api_url
            parts = device['api_url'].split()
            script_name = parts[0] 
            mode = parts[1].strip('-')

            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  
            script_path = os.path.join(base_dir, script_name) 
            device_ip = parts[2]
            device_name = device['device_name']

            command = ['/usr/bin/python3', script_path, mode, '--ip', device_ip, '--timeout', str(timeout)]

            try:
                # Execute the script with the appropriate parameters
                result = subprocess.run(
                    command,
                    capture_output=True,
                    text=True,
                    check=True
                )
                #print(colored(f"Debug: Script executed successfully, output: {result.stdout}", "green"))
                data = json.loads(result.stdout)  # Expecting JSON output from the script

                # Get the 'reachable' state and device name from the script output
                current_reachable = data.get('reachable', False)

            except subprocess.CalledProcessError as e:
                print(colored(f"Error executing {device['api_url']}: {e}", 'yellow'))
                print(colored(f"Debug: Subprocess error output: {e.stderr}", "red"))
                continue
            except json.JSONDecodeError as e:
                print(colored(f"Error parsing JSON from script output: {e}", 'yellow'))
                continue

            # Compare and log state changes
            db_reachable = bool(device['reachable'])
            if db_reachable != current_reachable:
                warning_msg = f"[Alert][{datetime.datetime.now()}][KeepAlive] Device '{device_name}' reachable changed! Database state: {db_reachable}, Current state: {current_reachable}"
                print(colored(warning_msg, 'red'))
                state_changes.append({
                    'api_url': device['api_url'],
                    'device_name': device_name,
                    'database_state': db_reachable,
                    'current_state': current_reachable
                })
        else:
            for device in devices:
                try:
                    response = requests.get(device['api_url'], verify=False, timeout=timeout)
                    data = response.json()
                    # 获取 'reachable' 状态
                    current_reachable = data.get('state', {}).get('reachable')
                    if current_reachable is None:
                        current_reachable = data.get('config', {}).get('reachable')
                    # 获取设备名称
                    device_name = device['device_name']

                    # 转换数据库中的状态
                    db_reachable = bool(device['reachable'])

                    if db_reachable != current_reachable:
                        warning_msg = f"[Alert][{datetime.datetime.now()}][KeepAlive] Device '{device_name}' reachable changed! Database state: {db_reachable}, Current state: {current_reachable}"
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
    #scan_interval, timeout, db_user, db_password, db_host, exclude_databases = load_config()
    config = load_config()  # 将配置加载为一个字典
    scan_interval = config['philips_hue_bridge_db']
    timeout = config['timeout']  # 根据实际键来访问
    db_user = config['db_user']
    db_password = config['db_password']
    db_host = config['db_host']
    exclude_databases = config['exclude_databases']

    conn = pymysql.connect(user=db_user, password=db_password, host=db_host)

    try:
        databases = get_databases(conn, exclude_databases)
        while True:
            for db_name in databases:
                devices = fetch_device_states(conn, db_name)
                check_devices(devices, timeout)
            time.sleep(scan_interval)
    finally:
        conn.close()

if __name__ == "__main__":
    main()

