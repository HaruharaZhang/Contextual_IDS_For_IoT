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
    executed_devices = set()  # 存储已执行脚本的设备IP
    devices_executed = False  # 标记是否已执行任何脚本

    while True:  # 添加循环以允许用户多次选择设备和脚本
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
        print("0. 进入模型选择页面")
        for idx, device in enumerate(devices):
            device_display = f"{idx + 1}. {device[2]} ({device[0]})"
            if device[0] in executed_devices:
                device_display = f"\033[92m{device_display}\033[0m"  # 绿色字体表示已执行
            print(device_display)

        # 用户选择设备
        try:
            choice = int(input(messages['select_device']))
            if choice == 0:
                if not devices_executed:
                    print("\033[91m请先选择至少一个设备并执行脚本。\033[0m")  # 使用红色字体提示
                    continue
                else:
                    break  # 退出循环进入模型加载部分
            elif choice < 0 or choice > len(devices):
                print(messages['invalid_choice'])
                continue

            choice -= 1  # 调整索引以匹配列表索引
            selected_device = devices[choice]
            device_ip = selected_device[0]
            os.environ["DEVICE_IP"] = device_ip
            executed_devices.add(device_ip)
            devices_executed = True
            print(f"Selected device IP {device_ip} has been stored in environment variable.")
        except ValueError:
            print("Invalid input. Please enter a number.")
            continue

        # 设备扫描脚本
        script_directory = 'Script'
        scripts = [f for f in os.listdir(script_directory) if f.endswith('.py')]
        print(messages['loading_scripts'])
        for idx, script in enumerate(scripts):
            print(f"{idx + 1}. {script}")

        script_choice = input(messages['select_script'])
        try:
            script_index = int(script_choice) - 1
            if script_index < 0 or script_index >= len(scripts):
                print(messages['invalid_choice'])
                continue

            script_path = os.path.join(script_directory, scripts[script_index])
            print(f"Running {script_path}...")
            subprocess.run([sys.executable, script_path], check=True)
            print("Script executed successfully.")
        except ValueError:
            print("Please enter a valid number.")
            continue
        except subprocess.CalledProcessError as e:
            print(f"Error executing {scripts[script_index]}: {e}")
            continue

    # 进入模型选择和加载
    model_directory = 'Model'
    models = [f for f in os.listdir(model_directory) if f.endswith('.py')]
    if not models:
        print("No model scripts found in the 'Model' directory.")
        return
    
    print("Available model scripts:")
    for idx, model in enumerate(models):
        print(f"{idx + 1}. {model}")

    model_choice = input("Enter the number of the model script you want to run: ")
    try:
        model_index = int(model_choice) - 1
        if model_index < 0 or model_index >= len(models):
            print("Invalid choice. Please select a valid model number.")
            return

        model_path = os.path.join(model_directory, models[model_index])
        print(f"Running {model_path}...")
        subprocess.run([sys.executable, model_path], check=True)
        print("Model script executed successfully.")
    except ValueError:
        print("Invalid input. Please enter a number.")
    except subprocess.CalledProcessError as e:
        print(f"Error executing {models[model_index]}: {e}")

if __name__ == "__main__":
    main()