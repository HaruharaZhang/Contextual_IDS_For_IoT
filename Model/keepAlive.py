import configparser
import time
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
    config.read('Config/Model/keepAlive.cfg')
    philips_hue_bridge_db = float(config['Settings']['philips_hue_bridge_db'])
    timeout = float(config['Settings']['timeout'])
    
    config.read('Config/database.cfg')
    db_user = config['Database']['user']
    db_password = config['Database']['password']
    db_host = config['Database']['host']
    exclude_databases = [db.strip() for db in config['Database']['exclude_databases'].split(',')]
    
    return philips_hue_bridge_db, timeout, db_user, db_password, db_host, exclude_databases

def get_databases(conn, exclude_databases):
    with conn.cursor() as cursor:
        cursor.execute("SHOW DATABASES;")
        databases = [db[0] for db in cursor.fetchall() if db[0].strip() not in exclude_databases]
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
                warning_msg = f"Alert: Device '{device_name}' reachable changed! Database state: {db_reachable}, Current state: {current_reachable}"
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
                    # 获取设备名称
                    device_name = device['device_name']

                    # 转换数据库中的状态
                    db_reachable = bool(device['reachable'])

                    if db_reachable != current_reachable:
                        warning_msg = f"Alert: Device '{device_name}' reachable changed! Database state: {db_reachable}, Current state: {current_reachable}"
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
    scan_interval, timeout, db_user, db_password, db_host, exclude_databases = load_config()
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

