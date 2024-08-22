import datetime
import nmap
import time
import configparser
import os
from datetime import datetime
from termcolor import colored

# 初始化Nmap Port Scanner
nm = nmap.PortScanner()

# 用于存储已知设备的字典
known_devices = {}

def load_config():
    config_path = os.path.join(os.path.dirname(__file__), '..', 'Config', 'Model', 'netNewDevice.cfg')
    config = configparser.ConfigParser()
    config.read(config_path, encoding='utf-8')  # 显式指定编码
    settings = config['Settings']
    return (settings['hosts'], float(settings['scan_interval']))

def initial_scan(hosts):
    # 扫描局域网内所有设备，这里的
    nm.scan(hosts, arguments='-sn') # 奇妙的bug，扫描两次才能扫到所有设备
    nm.scan(hosts, arguments='-sn')
    hosts_list = [(x, nm[x]['status']['state']) for x in nm.all_hosts()]
    known_devices.update(hosts_list)

def scan_network(hosts):
    # 扫描局域网内所有设备
    nm.scan(hosts, arguments='-sn')
    
    # 获取扫描结果中的所有主机
    hosts_list = [(x, nm[x]['status']['state']) for x in nm.all_hosts()]
    new_devices = {}
    for host, status in hosts_list:
        if status == 'up':
            # 检查设备是否为新设备
            if host not in known_devices:
                new_devices[host] = status
                print(colored(f"[Alert][{datetime.now()}][netNewDevice] New device found: {host}", 'red'))
                print(colored("Scanning new device", 'yellow'))
                scan_content = nm.scan(host, arguments='-A')
                filename = f"{host}_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.txt"
                save_path = os.path.join(os.path.dirname(__file__), '..', 'Log', 'Network', 'NewDevice', filename)
                os.makedirs(os.path.dirname(save_path), exist_ok=True)
                with open(save_path, 'w') as file:
                    file.write(str(scan_content))
                print(colored(f"Scan file saved to: /Log/Network/NewDevice/{filename}", 'yellow'))
                
    # 更新已知设备列表
    known_devices.update(new_devices)

def main():
    hosts, scan_interval=load_config()
    initial_scan(hosts)
    while True:
        scan_network(hosts)
        time.sleep(scan_interval)  # 每scan_interval分钟扫描一次

if __name__ == '__main__':
    main()
