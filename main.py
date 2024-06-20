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
    os.environ["LANGUAGE"] = lang

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
    try:
        choice = int(input(messages['select_device'])) - 1
        if choice < 0 or choice >= len(devices):
            print(messages['invalid_choice'])
            return

        selected_device = devices[choice]
        device_ip = selected_device[0]  # 假设设备的IP存储在列表的第一个元素
        os.environ["DEVICE_IP"] = device_ip  # 设置环境变量
        print(f"Selected device IP {device_ip} has been stored in environment variable.")
    except ValueError:
        print("Invalid input. Please enter a number.")
    except IndexError:
        print("No device at this number. Please enter a valid device number.")

    # 设备扫描脚本
    script_directory = 'Script'
    scripts = [f for f in os.listdir(script_directory) if f.endswith('.py')]
    print(messages['loading_scripts'])
    for idx, script in enumerate(scripts):
        print(f"{idx + 1}. {script}")

    # 用户选择脚本
    script_choice = input(messages['select_script'])
    try:
        script_index = int(script_choice) - 1
        if script_index < 0 or script_index >= len(scripts):
            print(messages['invalid_choice'])
            return

        # 运行选定的脚本
        script_path = os.path.join('Script', scripts[script_index])
        print(f"Running {script_path}...")
        subprocess.run([sys.executable, script_path], check=True)
        print("Script executed successfully.")
    except ValueError:
        print("Please enter a valid number.")
    except subprocess.CalledProcessError as e:
        print(f"Error executing {scripts[script_index]}: {e}")

    
    # Model加载
    try:
        script_directory = 'Model'  # 设定脚本所在的目录
        scripts = [f for f in os.listdir(script_directory) if f.endswith('.py')]
        if not scripts:
            print("No scripts found in the 'Model' directory.")
            return
        
        print("Available scripts in the 'Model' directory:")
        for idx, script in enumerate(scripts):
            print(f"{idx + 1}. {script}")
        
        script_choice = input("Enter the number of the script you want to run: ")
        script_index = int(script_choice) - 1
        
        if script_index < 0 or script_index >= len(scripts):
            print("Invalid choice. Please select a valid script number.")
            return
        
        script_path = os.path.join(script_directory, scripts[script_index])
        print(f"Running {script_path}...")
        subprocess.run([sys.executable, script_path], check=True)
        print("Script executed successfully.")
    except ValueError:
        print("Invalid input. Please enter a number.")
    except subprocess.CalledProcessError as e:
        print(f"Error executing {scripts[script_index]}: {e}")

if __name__ == "__main__":
    main()
