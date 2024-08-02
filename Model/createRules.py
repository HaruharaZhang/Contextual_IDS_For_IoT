import configparser
import time
import datetime
import os
import requests
import pymysql
import subprocess
import json
import pytz  # 引入pytz处理时区
from termcolor import colored
from datetime import datetime, timedelta

def load_config():
    # 读取 createRules.cfg 配置文件
    keep_alive_path = os.path.join(os.path.dirname(__file__), '..', 'Config', 'Model', 'createRules.cfg')
    config = configparser.ConfigParser()
    read_files = config.read(keep_alive_path, encoding='utf-8')  # 显式指定编码

    if not read_files:
        print("Failed to read createRules configuration file, please check the path and encoding.")
        return None
    
    try:
        database_scan_interval = int(config['Settings']['database_scan_interval'])
        default_rule_threshold = int(config['Settings']['default_rule_threshold'])
        button_press_interval = float(config['Settings']['button_press_interval'])
        socket_voltage_threshold = float(config['Settings']['socket_voltage_threshold'])
        socket_voltage_min = float(config['Settings']['socket_voltage_min'])
        socket_voltage_max = float(config['Settings']['socket_voltage_max'])
        sensor_temperature_threshold = float(config['Settings']['sensor_temperature_threshold'])
        sensor_light_threshold = int(config['Settings']['sensor_light_threshold'])
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
        'database_scan_interval': database_scan_interval,
        'default_rule_threshold': default_rule_threshold,
        'button_press_interval': button_press_interval,
        'socket_voltage_threshold': socket_voltage_threshold,
        'socket_voltage_min': socket_voltage_min,
        'socket_voltage_max': socket_voltage_max,
        'sensor_temperature_threshold': sensor_temperature_threshold,
        'sensor_light_threshold': sensor_light_threshold,
        'db_user': db_user,
        'db_password': db_password,
        'db_host': db_host,
        'exclude_databases': exclude_databases
    }

def get_databases(conn, exclude_databases):
    with conn.cursor() as cursor:
        cursor.execute("SHOW DATABASES;")
        databases = [db[0] for db in cursor.fetchall() if db[0].strip() not in exclude_databases]
    return databases

def fetch_device_states(conn, db_name):
    conn.select_db(db_name)
    with conn.cursor(pymysql.cursors.DictCursor) as cursor:
        cursor.execute("SELECT device_name, state FROM device_states;")
        devices = cursor.fetchall()
    return devices

def add_sensor_values(sensor_light_threshold, sensor_temperature_threshold):
    resuit = []
    light_command = ['python', os.path.join(os.path.dirname(__file__), '..', 'Connector', 'Elegoo_Mega2560.py'), '-l']
    temperature_command = ['python', os.path.join(os.path.dirname(__file__), '..', 'Connector', 'Elegoo_Mega2560.py'), '-t']

    try:
        light_output = subprocess.run(light_command, capture_output=True, text=True, timeout=5)
        if light_output.stdout:
            light_value = int(light_output.stdout.strip().split(': ')[1])
            if light_value > sensor_light_threshold:
                light_value = "light_sensor_high"
            else:
                light_value = "light_sensor_normal"
            resuit.append(light_value)
    except subprocess.TimeoutExpired:
        print("Timeout while reading light sensor")
    except Exception as e:
        print(f"Failed to read light sensor: {str(e)}")

    try:
        temperature_output = subprocess.run(temperature_command, capture_output=True, text=True, timeout=5)
        if temperature_output.stdout:
            temperature_value = float(temperature_output.stdout.strip().split(': ')[1])
            if(temperature_value > sensor_temperature_threshold):
                temperature_value = "temputer_sensor_high"
            else:
                temperature_value = "temputer_sensor_normal"
            resuit.append(temperature_value)
    except subprocess.TimeoutExpired:
        print("Timeout while reading temperature sensor")
    except Exception as e:
        print(f"Failed to read temperature sensor: {str(e)}")

    return resuit

def create_rule(devices, button_press_interval, socket_voltage_threshold, socket_voltage_min, socket_voltage_max):
    prolog_rules = []
    # 解析设备数据，并构建规则
    for device in devices:
        device_name = device['device_name']
        device_state_json = device['state'] # 如果出现state不存在的情况，需要额外处理
        device_state = json.loads(device_state_json)

        # For Hue white lamp
        try:
            if device_state['productname'] == "Hue white lamp":
                prolog_rules.append(device_state['state']['on'])
                prolog_rules.append(device_state['state']['bri'])
                prolog_rules.append(device_state['state']['reachable'])
                prolog_rules.append(device_state['uniqueid']) 
        except Exception as e:
            pass

         # For Hue Smart button
        try:
            if device_state['productname'] == "Hue Smart button":
                prolog_rules.append(device_state['state']['buttonevent'])
                #prolog_rules.append(device_state['state']['lastupdated'])
                
                # 设置当前时间为UTC时间，数据库时间也是UTC
                current_time = datetime.utcnow().replace(tzinfo=pytz.utc)
                # 检查开关是否在最近x秒内被按下
                if current_time - datetime.strptime(device_state['state']['lastupdated'], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=pytz.utc) <= timedelta(seconds=button_press_interval):
                    prolog_rules.append('switch_pressed')
                else:
                    prolog_rules.append('switch_unpressed')
                #witch_state = 'switch_pressed' if any(current_time - datetime.strptime(s['last_event_time'], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=pytz.utc) <= timedelta(seconds=8.5) for s in switches) else 'switch_unpressed'
    
                prolog_rules.append(device_state['state']['reachable'])
                prolog_rules.append(device_state['uniqueid']) 
        except Exception as e:
            pass

        # For dimDirection
        try:
            if device_name == "dimDirection":
                prolog_rules.append(device_state['uniqueid'])
                prolog_rules.append(device_state['config']['on'])
                prolog_rules.append(device_state['config']['reachable'])
                if current_time - datetime.strptime(device_state['state']['lastupdated'], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=pytz.utc) <= timedelta(seconds=button_press_interval):
                    prolog_rules.append(True)
                else:
                    prolog_rules.append(False)
        except Exception as e:
            pass

        # For isDimming
        try:
            if device_name == "isDimming":
                prolog_rules.append(device_state['uniqueid'])
                prolog_rules.append(device_state['config']['on'])
                prolog_rules.append(device_state['config']['reachable'])
                if current_time - datetime.strptime(device_state['state']['lastupdated'], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=pytz.utc) <= timedelta(seconds=button_press_interval):
                    prolog_rules.append(True)
                else:
                    prolog_rules.append(False)
        except Exception as e:
            pass
        
        # For slotState
        try:
            if device_name == "slotState":
                prolog_rules.append(device_state['uniqueid'])
                prolog_rules.append(device_state['config']['on'])
                prolog_rules.append(device_state['config']['reachable'])
                if current_time - datetime.strptime(device_state['state']['lastupdated'], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=pytz.utc) <= timedelta(seconds=button_press_interval):
                    prolog_rules.append(True)
                else:
                    prolog_rules.append(False)
        except Exception as e:
            pass

        # For cycling
        try:
            if device_name == "cycling":
                prolog_rules.append(device_state['uniqueid'])
                prolog_rules.append(device_state['config']['on'])
                prolog_rules.append(device_state['config']['reachable'])
                if current_time - datetime.strptime(device_state['state']['lastupdated'], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=pytz.utc) <= timedelta(seconds=button_press_interval):
                    prolog_rules.append(True)
                else:
                    prolog_rules.append(False)
        except Exception as e:
            pass

        # For TP-Link Smart Wi-Fi Plug Mini with Energy Monitoring
        try:
            if device_state['dev_name'] == "Smart Wi-Fi Plug Mini" and device_state['model'] == "KP115(UK)" and device_state['mic_type'] == "IOT.SMARTPLUGSWITCH":
                prolog_rules.append(device_state['deviceId'])
                if(device_state['current_ma'] > socket_voltage_threshold):
                    prolog_rules.append(True)
                else:
                    prolog_rules.append(False)
                prolog_rules.append(device_state['relay_state'])
                if(device_state['voltage_mv'] > socket_voltage_min and device_state['voltage_mv'] < socket_voltage_max):
                    prolog_rules.append(True)
                else:
                    prolog_rules.append(False)
        except Exception as e:
            pass

        # For TP-LINK_Power Strip_3A1B
        try:
            if device_state['alias'] == "TP-LINK_Power Strip_3A1B" and device_state['model'] == "KP303(UK)" and device_state['mic_type'] == "IOT.SMARTPLUGSWITCH":
                prolog_rules.append(device_state['deviceId'])

                prolog_rules.append(device_state['children'][0]['id'])
                prolog_rules.append(device_state['children'][0]['state'])
                prolog_rules.append(device_state['children'][1]['id'])
                prolog_rules.append(device_state['children'][1]['state'])
                prolog_rules.append(device_state['children'][2]['id'])
                prolog_rules.append(device_state['children'][2]['state'])

        except Exception as e:
            pass
    return prolog_rules
        
def add_prolog_rules(rule):
    prolog_rule = "valid_state(["
    for i in range(len(rule)):
        if i == 0:
            prolog_rule += "'" + str(rule[i]) + "'"
        elif i == len(rule) - 1:
            prolog_rule += ", " + "'" + str(rule[i]) + "'" + "])."
        else:
            prolog_rule += ", " + "'" + str(rule[i]) + "'"
    # 将规则写入到Prolog文件
    with open(os.path.join(os.path.dirname(__file__), '..', 'Prolog', 'auto_rules.pl'), 'a') as f:
        f.write(prolog_rule + '\n')
    print(colored("Rule added to Prolog file", "green"))

def main():
    config = load_config()  # 将配置加载为一个字典
    database_scan_interval = config['database_scan_interval']
    default_rule_threshold = config['default_rule_threshold']
    button_press_interval = config['button_press_interval']
    socket_voltage_threshold = config['socket_voltage_threshold']
    socket_voltage_min = config['socket_voltage_min']
    socket_voltage_max = config['socket_voltage_max']
    sensor_light_threshold = config['sensor_light_threshold']
    sensor_temperature_threshold = config['sensor_temperature_threshold']
    db_user = config['db_user']
    db_password = config['db_password']
    db_host = config['db_host']
    exclude_databases = config['exclude_databases']

    # 初始化变量
    rule_count = {}
    prolog_rules_all = []
    new_rule = []
    rules_list = []
    prolog_rules_all_count = []
    prolog_rules_all_isAdd = []
    
    
    try:
        while True:
            conn = pymysql.connect(user=db_user, password=db_password, host=db_host)
            databases = get_databases(conn, exclude_databases)
            new_rule = [] # 清空数组内容
            for db_name in databases:
                devices = fetch_device_states(conn, db_name)
                new_rule.extend(create_rule(devices, button_press_interval, socket_voltage_threshold, socket_voltage_min, socket_voltage_max))
            #new_rule.extend(add_sensor_values(sensor_light_threshold, sensor_temperature_threshold))
            light_and_temperature = add_sensor_values(sensor_light_threshold, sensor_temperature_threshold)
            new_rule.append(light_and_temperature[0])
            new_rule.append(light_and_temperature[1])

            if(new_rule in prolog_rules_all):
                index = prolog_rules_all.index(new_rule)
                if(prolog_rules_all_count[index] > default_rule_threshold):
                    if(prolog_rules_all_isAdd[index] == False):
                        prolog_rules_all_isAdd[index] = True
                        add_prolog_rules(new_rule)
                        print(colored("Add new rule: " + str(new_rule), "green"))
                else:  
                    prolog_rules_all_count[index] += 1

            else:
                prolog_rules_all.append(new_rule)
                prolog_rules_all_count.append(1)
                prolog_rules_all_isAdd.append(False)


            # 清空rules
            rule_count = {}
            time.sleep(database_scan_interval)
            conn.close()
    finally:
        conn.close()


if __name__ == "__main__":
    main()