import requests
import os
import pymysql
from configparser import ConfigParser

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

def defind_runner():
    dbname = 'philips_hue_bridge_db'
    fetch_and_store_data()

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
        #print(messages[f'{endpoint}_stored'])
    else:
        print(messages[f'{endpoint}_failed'], response.status_code, response.text)

def defind_runner():
    fetch_and_store_data()

def main():
    defind_runner

if __name__ == "__main__":
    main()