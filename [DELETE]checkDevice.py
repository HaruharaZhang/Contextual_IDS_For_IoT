import os
import sys
import json
import nmap
from prettytable import PrettyTable
from messageLoader import get_messages

def format_scan_result(result, messages, device_name):
    """格式化扫描结果，并查找匹配的操作系统信息"""
    # 输出调试信息到标准错误，不影响标准输出的JSON结果
    print("\n" + "="*60, file=sys.stderr)
    print(messages['scan_summary'], file=sys.stderr)

    # IP和MAC地址
    addresses = result.get('addresses', {})
    print(f"IP Address: {addresses.get('ipv4', 'N/A')}", file=sys.stderr)
    print(f"MAC Address: {addresses.get('mac', 'N/A')}", file=sys.stderr)

    # 供应商信息
    vendor = result.get('vendor', {}).get(addresses.get('mac', ''), 'N/A')
    print(f"Vendor: {vendor}", file=sys.stderr)

    # 主机名
    hostnames = result.get('hostnames', [{'name': 'N/A'}])
    print(f"Hostnames: {', '.join([h['name'] for h in hostnames])}", file=sys.stderr)

    # 端口信息
    print("\n" + messages['open_ports'], file=sys.stderr)
    ports = result.get('tcp', {})
    table = PrettyTable(["Port", "State", "Service", "Product", "Version", "Extra Info"])
    for port, port_data in ports.items():
        table.add_row([
            port,
            port_data.get('state', 'N/A'),
            port_data.get('name', 'N/A'),
            port_data.get('product', 'N/A'),
            port_data.get('version', 'N/A'),
            port_data.get('extrainfo', 'N/A')
        ])
    print(table, file=sys.stderr)

    # 操作系统匹配
    print("\n" + messages['os_match'], file=sys.stderr)
    osmatches = result.get('osmatch', [])
    selected_os = None
    highest_match_score = 0

    device_words = set(device_name.lower().split())
    
    for match in osmatches:
        os_name = match.get('name', 'N/A')
        accuracy = match.get('accuracy', 'N/A')

        # 计算匹配分数
        os_words = set(word for word in os_name.lower().split() if word.isalpha())
        match_score = len(device_words & os_words)

        if match_score > highest_match_score:
            highest_match_score = match_score
            selected_os = os_name

    return selected_os

def check_device(device, messages):
    """进一步扫描设备"""
    #print(messages['scanning_device'].format(vendor=device[2], mac=device[1], host=device[0]), file=sys.stderr)
    nm = nmap.PortScanner()
    nm.scan(hosts=device[0], arguments='-sV -O')  # 服务版本扫描和操作系统识别
    return nm[device[0]]

if __name__ == "__main__":
    device = json.loads(os.environ["DEVICE"])
    lang = os.environ["LANGUAGE"]
    messages = get_messages(lang)
    
    result = check_device(device, messages)
    selected_os = format_scan_result(result, messages, device[2])
    
    output = {
        "selected_os": selected_os,
        "device_ip": device[0]
    }

    # 仅输出JSON结果
    print(json.dumps(output))
