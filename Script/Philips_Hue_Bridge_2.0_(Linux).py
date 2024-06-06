import requests
import json
import urllib3

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

    # 跳过证书验证发送 POST 请求
    response = requests.post(url, headers=headers, data=json.dumps(body), verify=False)

    if response.status_code == 200:
        print("User created successfully:", response.json())
    else:
        print("Failed to create user:", response.status_code, response.text)

def get_data(device_ip):
    """获取设备数据并创建用户"""
    ip = device_ip
    print(f"Debug: Retrieved DEVICE_IP = {ip}")
    if not ip:
        raise ValueError("No IP address provided.")

    print(f"Creating user on Philips Hue Bridge at {ip}...")
    create_hue_user(ip)

if __name__ == "__main__":
    # 获取 DEVICE_IP 参数
    # device_ip = globals().get('DEVICE_IP')
    # get_data(device_ip)
    print()