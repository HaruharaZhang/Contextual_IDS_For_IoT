import os
import sys
import ctypes
import subprocess
import json
from messageLoader import get_messages

# 确保当前目录在系统路径中以便导入 getDevice
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from getDevice import scan_network

def is_admin():
    """检查是否具有管理员权限"""
    try:
        return os.getuid() == 0
    except AttributeError:
        # Windows 环境下使用 ctypes 检查
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False

def main():
    # 选择语言
    print("请选择一种语言:")
    print("1. 中文")
    print("2. English")
    choice = input().strip()

    if choice == '1':
        lang = 'zh'
    elif choice == '2':
        lang = 'en'
    else:
        print("选择无效。默认使用英语。")
        lang = 'en'

    messages = get_messages(lang)

    if not is_admin():
        print(messages['admin_required'])
        sys.exit()

    # 显示欢迎信息
    print(messages['welcome'])

    # 让用户输入扫描网段
    print(messages['enter_network_with_default'])
    network = input().strip()
    if not network:
        network = '192.168.88.0/24'
        print(messages['using_default_network'])

    # 加载并显示设备数据
    print(messages['loading_scripts'])
    devices = scan_network(messages, network)
    
    # 显示设备选择菜单
    print(messages['device_menu'])
    for idx, device in enumerate(devices):
        print(f"{idx + 1}. {device[2]} ({device[0]})")
    
    # 用户选择设备
    choice = int(input(messages['select_device'])) - 1
    if choice < 0 or choice >= len(devices):
        print(messages['invalid_choice'])
        return

    selected_device = devices[choice]
    print(messages['scanning_device'].format(vendor=selected_device[2], mac=selected_device[1], host=selected_device[0]))

    # 使用当前的 Python 解释器调用 `checkDevice.py` 并捕获其输出
    env = os.environ.copy()
    env["DEVICE"] = json.dumps(selected_device)
    env["LANGUAGE"] = lang

    try:
        check_device_output = subprocess.check_output([sys.executable, "checkDevice.py"], env=env, universal_newlines=True)
        check_device_result = json.loads(check_device_output)

        selected_os = check_device_result.get("selected_os")
        device_ip = check_device_result.get("device_ip")

        if selected_os and device_ip:
            script_name = f"{selected_os.replace(' ', '_')}.py"
            script_path = os.path.join('Script', script_name)
            
            if os.path.exists(script_path):
                print(messages['found_script'].format(script=script_path))
                # 加载并执行脚本
                exec(open(script_path).read(), {'__name__': '__main__', 'DEVICE_IP': device_ip})
            else:
                print(messages['not_found_script'].format(script=script_name))
        else:
            print(messages['no_os_match'])
    except subprocess.CalledProcessError as e:
        print(f"Error executing checkDevice.py: {e}")
        print(f"Output: {e.output}")

if __name__ == "__main__":
    main()
