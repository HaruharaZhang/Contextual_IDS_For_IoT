#!/usr/bin/env python3

import argparse
import socket
import json
from struct import pack, unpack

def encrypt(string):
    key = 171
    result = pack(">I", len(string))
    for i in string:
        a = key ^ ord(i)
        key = a
        result += bytes([a])
    return result

def decrypt(string):
    key = 171
    result = ""
    for i in string:
        a = key ^ i
        key = i
        result += chr(a)
    return result

def send_command(ip, port, timeout, cmd):
    try:
        sock_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock_tcp.settimeout(timeout)
        sock_tcp.connect((ip, port))
        sock_tcp.send(encrypt(cmd))
        data = sock_tcp.recv(2048)
        sock_tcp.close()

        return decrypt(data[4:])
    except socket.error as e:
        return json.dumps({"error": str(e)})

def main():
    parser = argparse.ArgumentParser(description="TP-Link Smart Plug Client")
    parser.add_argument("mode", choices=["main", "children"], help="Operational mode: 'main' or 'children'")
    parser.add_argument("--ip", required=True, help="IP address of the smart plug")
    parser.add_argument("--port", type=int, default=9999, help="Port number, default 9999")
    parser.add_argument('--timeout', type=float, required=False, default=10, help='Timeout in seconds(float)')
    args = parser.parse_args()

    info_command = '{"system":{"get_sysinfo":{}}}'
    response = send_command(args.ip, args.port, args.timeout, info_command)
    response_data = json.loads(response)

    if args.mode == "main":
        err_code = response_data.get("system", {}).get("get_sysinfo", {}).get("err_code", 1)
        reachable = 1 if err_code == 0 else 0
        alias = response_data.get("system", {}).get("get_sysinfo", {}).get("alias") 
        print(json.dumps({"reachable": reachable, "name": alias}))

    elif args.mode == "children":
        children = response_data.get("system", {}).get("get_sysinfo", {}).get("children", [])
        children_info = [{"id": child["id"], "state": child["state"], "name": child["alias"]} for child in children]
        print(json.dumps({"children": children_info}))

if __name__ == "__main__":
    main()
