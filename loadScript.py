import subprocess
import json
import os
from messageLoader import get_messages

def load_and_execute_script(script_name, device_ip):
    """加载并执行指定脚本"""
    script_path = os.path.join('Script', script_name)
    if os.path.exists(script_path):
        print(f"Debug: Found script {script_path}")
        exec(open(script_path).read(), {'__name__': '__main__', 'DEVICE_IP': device_ip})
    else:
        print(f"Debug: Script {script_path} not found")

def main():
    lang = os.environ.get("LANGUAGE", "en")
    messages = get_messages(lang)

    # 假设 `get_devices.py` 返回网络中的所有设备
    get_devices_output = subprocess.check_output(["python3", "getDevice.py"], universal_newlines=True)
    devices = json.loads(get_devices_output)
    
    # 显示设备选择菜单
    print(messages['device_menu'])
    for idx, device in enumerate(devices):
        print(f"{idx + 1}. {device['vendor']} ({device['ip']})")
    
    # 用户选择设备
    choice = int(input(messages['select_device'])) - 1
    if choice < 0 or choice >= len(devices):
        print(messages['invalid_choice'])
        return

    selected_device = devices[choice]
    print(messages['scanning_device'].format(vendor=selected_device['vendor'], mac=selected_device['mac'], host=selected_device['ip']))

    # 设置环境变量
    os.environ["DEVICE"] = json.dumps(selected_device)
    os.environ["LANGUAGE"] = lang

    # 调用 `checkDevice.py` 并捕获其输出
    check_device_output = subprocess.check_output(["python3", "checkDevice.py"], universal_newlines=True, env=os.environ.copy())
    print(f"Debug: Output from checkDevice.py: {check_device_output}")
    
    check_device_result = json.loads(check_device_output)

    selected_os = check_device_result.get("selected_os")
    device_ip = check_device_result.get("device_ip")

    print(f"Debug: selected_os = {selected_os}, device_ip = {device_ip}")

    if selected_os and device_ip:
        script_name = f"{selected_os.replace(' ', '_').replace('.', '_').replace('(', '').replace(')', '')}.py"
        if os.path.exists(os.path.join('Script', script_name)):
            print(messages['found_script'].format(script=script_name))
            # 加载并执行脚本
            load_and_execute_script(script_name, device_ip)
        else:
            print(messages['not_found_script'].format(script=script_name))
    else:
        print(messages['no_os_match'])

if __name__ == "__main__":
    main()
