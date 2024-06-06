import os
import nmap
from prettytable import PrettyTable
import socket
from messageLoader import get_messages

def get_local_ip():
    """获取本机的局域网IP地址"""
    try:
        # 尝试通过连接到一个外部IP地址来获取局域网IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0)
        s.connect(('8.8.8.8', 80))
        local_ip = s.getsockname()[0]
    except Exception:
        # 通过其他方法获取本地IP地址
        local_ip = '127.0.0.1'
        try:
            # 尝试获取所有网络接口的IP地址
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            if local_ip.startswith("127.") or not local_ip:
                # 如果获取到的IP地址是127.x.x.x或为空，尝试使用其他方法
                interfaces = os.popen('ifconfig | grep "inet " | grep -v 127.0.0.1').read().strip().split('\n')
                for iface in interfaces:
                    ip = iface.strip().split(' ')[1]
                    if ip:
                        local_ip = ip
                        break
        except Exception:
            pass
    finally:
        s.close()
    return local_ip

def scan_network(messages, network):
    """使用 nmap 扫描网络中的设备"""
    print(messages['scanning_network'])
    nm = nmap.PortScanner()
    nm.scan(hosts=network, arguments='-sn -PR')  # 使用用户输入的网络范围进行扫描

    local_ip = get_local_ip()

    # 生成表格以显示扫描结果
    table = PrettyTable()
    table.field_names = ["IP Address", "MAC Address", "Vendor"]
    
    hosts_list = []
    for host in nm.all_hosts():
        mac = nm[host]['addresses'].get('mac', 'N/A')
        vendor = nm[host].get('vendor', {}).get(mac, 'N/A')
        if host != local_ip:
            hosts_list.append((host, mac, vendor))
            table.add_row([host, mac, vendor])
    
    print(messages['devices_found'])
    print(table)
    
    return hosts_list

if __name__ == "__main__":
    lang = os.environ.get("LANGUAGE", "en")
    messages = get_messages(lang)

    network = '192.168.88.0/24'  # 默认网段
    devices = scan_network(messages=messages, network=network)
