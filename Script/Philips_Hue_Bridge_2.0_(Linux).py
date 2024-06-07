import requests
import json
import time
import urllib3
import os
from messageLoader import get_messages

# 忽略不安全请求警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def create_hue_user(ip):
    """创建 Philips Hue 用户"""
    url = f"https://{ip}/api"
    body = {
        "devicetype": "my_hue_app#samsung_A32"
    }
    headers = {
        "Content-Type": "application/json"
    }

    while True:
        # 跳过证书验证发送 POST 请求
        response = requests.post(url, headers=headers, data=json.dumps(body), verify=False)
        response_json = response.json()

        if response.status_code == 200 and "error" in response_json[0]:
            error = response_json[0]["error"]
            if error["type"] == 101 and "link button not pressed" in error["description"]:
                print(messages['press_button'])
                time.sleep(1)
            else:
                print("出现其他错误:", error["description"])
                break
        elif response.status_code == 200:
            print("User created successfully:", response_json)
            break
        else:
            print("Failed to create user:", response.status_code, response.text)
            break

def get_data(device_ip):
    """获取设备数据并创建用户"""
    print(f"Debug: get_data called with device_ip = {device_ip}")  # 添加调试信息
    ip = device_ip
    if not ip:
        raise ValueError("No IP address found in environment variables.")
    create_hue_user(ip)

if __name__ == "__main__":
    lang = os.environ.get("LANGUAGE", "en")
    messages = get_messages(lang)
    # 获取 DEVICE_IP 参数
    device_ip = os.getenv('DEVICE_IP')
    # print(f"Debug: Retrieved DEVICE_IP = {device_ip}")  # 添加调试信息
    get_data(device_ip)
