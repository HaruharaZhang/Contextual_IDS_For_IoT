import configparser
import time
import datetime
import os
import requests
import pymysql
import subprocess # 引入subprocess处理命令行调用
import json # 引入json处理设备状态
import pytz  # 引入pytz处理时区
from termcolor import colored
from datetime import datetime, timedelta
import subprocess

from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# 全局变量，用于跟踪上一次的检查结果
last_state = None

# 从配置文件中读取数据库配置
def get_db_config():
    # 定义配置文件路径
    config_path = os.path.join(os.path.dirname(__file__), '..', 'Config', 'database.cfg')

    # 创建配置解析器并读取配置文件
    config = configparser.ConfigParser()
    read_files = config.read(config_path, encoding='utf-8')  # 显式指定编码
    if not read_files:
        print("Failed to read any configuration files, please check the path and encoding.")
        return None

    # 尝试获取数据库配置
    try:
        db_config = {
            'host': config['Database']['host'],
            'port': int(config['Database']['port']),
            'user': config['Database']['user'],
            'password': config['Database']['password']
        }
    except KeyError as e:
        print("Key error:", e, "Check your configuration file sections and keys.")
        return None
    except Exception as e:
        print("An error occurred while parsing the database configuration:", str(e))
        return None

    return db_config

def load_config():
    config_path = os.path.join(os.path.dirname(__file__), '..', 'Config', 'Model', 'lightControl.cfg')
    config = configparser.ConfigParser()
    config.read(config_path, encoding='utf-8')  # 显式指定编码
    settings = config['Settings']

    return (float(settings['timeout']), settings['database'], float(settings['scan_interval']))

def get_sensor_values():
    result = {}
    light_command = ['python', os.path.join(os.path.dirname(__file__), '..', 'Connector', 'Elegoo_Mega2560.py'), '-l']
    temperature_command = ['python', os.path.join(os.path.dirname(__file__), '..', 'Connector', 'Elegoo_Mega2560.py'), '-t']

    try:
        # 获取光照度，设置超时时间为10秒
        #print("Reading light sensor...")
        light_output = subprocess.run(light_command, capture_output=True, text=True, timeout=5)
        #light_output = subprocess.run(light_command, text=True, timeout=5)
        #print(light_output.stdout)
        if light_output.stdout:
            light_value = int(light_output.stdout.strip().split(': ')[1])
            result['light'] = light_value
            #print(f"Light sensor value: {light_value}")
    except subprocess.TimeoutExpired:
        print("Timeout while reading light sensor")
    except Exception as e:
        print(f"Failed to read light sensor: {str(e)}")

    try:
        # 获取温度，设置超时时间为10秒
        #print("Reading temperature sensor...")
        temperature_output = subprocess.run(temperature_command, capture_output=True, text=True, timeout=5)
        #print(temperature_output.stdout)
        if temperature_output.stdout:
            temperature_value = float(temperature_output.stdout.strip().split(': ')[1])
            result['temperature'] = temperature_value
            #print(f"Temperature sensor value: {temperature_value}")
    except subprocess.TimeoutExpired:
        print("Timeout while reading temperature sensor")
    except Exception as e:
        print(f"Failed to read temperature sensor: {str(e)}")

    return result

def fetch_device_states(db_name):
    db_config = get_db_config()
    conn = pymysql.connect(
        host=db_config['host'],
        port=db_config['port'],
        user=db_config['user'],
        password=db_config['password'],
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )
    db_names = db_name.split(',')
    devices = []
    for name in db_names:
        conn.select_db(name.strip())
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("SELECT * FROM device_states;")
            devices.extend(cursor.fetchall())
    return devices

# 获取所有数据库中的设备状态，通过prolog runner 查询他们之间的关系是否符合规则
def check_devices(devices):
    lamps = []
    switches = []
    sockets = []   
    for device in devices:
        state_info = json.loads(device['state'])
        if 'state' in state_info and isinstance(state_info['state'], dict):
            if 'bri' in state_info['state']:  # 灯泡状态
                lamps.append(state_info['state']['on'])
            elif 'buttonevent' in state_info['state']:  # 开关状态
                switch_state = {
                    'device_name': device['device_name'],
                    'last_event_time': state_info['state']['lastupdated']
                }
                switches.append(switch_state)
        
        if 'children' in state_info:  # 插座状态
            socket_on = any(child['state'] == 1 for child in state_info['children'])
            sockets.append(socket_on)

    # 设置当前时间为UTC时间，假设数据库时间也是UTC
    current_time = datetime.utcnow().replace(tzinfo=pytz.utc)

    # 分析灯泡、开关、插座的状态，转化为prolog需要的参数格式
    bulb_state = 'bulb_on' if any(lamps) else 'bulb_off'
    # 检查开关是否在最近x秒内被按下
    switch_state = 'switch_pressed' if any(current_time - datetime.strptime(s['last_event_time'], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=pytz.utc) <= timedelta(seconds=8.5) for s in switches) else 'switch_unpressed'
    socket_state = 'socket_on' if any(sockets) else 'socket_off'
    #print(colored(f"Bulb: {bulb_state}, Switch: {switch_state}, Socket: {socket_state}", 'green'))

    # 传感器状态
    sensor_data = get_sensor_values()
    light_level = sensor_data.get('light', '0')
    temperature = sensor_data.get('temperature', '0')
    print(colored(f"Bulb: {bulb_state}, Switch: {switch_state}, Socket: {socket_state}, Light: {light_level}, Temperature: {temperature}", 'green'))
    light_level = 'sensor_high' if int(light_level) > 600 else 'sensor_low'

    # 调用 Prolog 脚本
    output = call_prolog_script('rules', bulb_state, switch_state, socket_state, "high_voltage", light_level)
    check_and_alert(output)
    print(output)

def check_and_alert(current_output):
    global last_state
    # 将当前的输出与上次的输出进行比较
    if last_state == False and current_output == False:
        # 连续两次输出为False，触发警报
        warning_msg = f"[Alert][{datetime.datetime.now()}][LightControl] Device reachable changed! Database state: False, Current state: False"
        print(colored(warning_msg, 'red'))
    # 更新上次的状态为当前状态
    last_state = current_output

# 调用 prolog_runner.py 脚本，查询设备之间的关系
def call_prolog_script(name, bulb, switch, socket, voltage, sensor):
    # 构造命令行调用
    # 'python', '../prolog_script_runner.py',
    command = [
        'python', os.path.join(os.path.dirname(__file__), '..', 'prolog_script_runner.py'),
        '--name', name,
        '--bulb', bulb,
        '--switch', switch,
        '--socket', socket,
        '--voltage', voltage,
        '--sensor', sensor
    ]
    # 执行命令
    result = subprocess.run(command, capture_output=True, text=True)
    return result.stdout

def main():
    timeout, db_name, scan_interval=load_config()

    while True:
        devices = fetch_device_states(db_name)
        check_devices(devices)
        time.sleep(scan_interval)

if __name__ == "__main__":
    main()

