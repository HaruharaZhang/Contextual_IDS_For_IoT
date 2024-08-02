import serial
import time
import configparser
import os
import argparse
from serial.tools import list_ports

def load_config():
    config_path = os.path.join(os.path.dirname(__file__), '..', 'Config', 'Connector', 'Elegoo_Mega2560.cfg')
    config = configparser.ConfigParser()
    config.read(config_path)
    return config['DEFAULT']

def list_serial_ports():
    ports = list_ports.comports()
    available_ports = [port.device for port in ports]
    print("Available serial ports:")
    for port in available_ports:
        print(port)
    return available_ports

def send_command(ser, command):
    """ 发送命令到Arduino """
    ser.write((command + "\n").encode())  # 发送命令字符串，后跟换行符
    time.sleep(0.5)  # 稍等一会，确保Arduino有时间处理命令

def parse_arguments():
    parser = argparse.ArgumentParser(description="Read temperature and light sensor values from a serial port.")
    parser.add_argument("-t", "--temperature", help="Read and return temperature value.", action="store_true")
    parser.add_argument("-l", "--light", help="Read and return light sensor value.", action="store_true")
    parser.add_argument("-a", "--alert", type=str, help="Send an alert type (e.g., NORMAL, WARNING, ALERT)")
    return parser.parse_args()

def main():
    args = parse_arguments()
    config = load_config()

    port = config.get('port')
    baudrate = config.getint('baudrate')
    interval = config.getfloat('interval')

    try:
        ser = serial.Serial(port, baudrate, timeout=1)
        if args.alert:
            print(f"Sending alert: {args.alert}")
            time.sleep(1)
            send_command(ser, args.alert)
            ser.close()  # 关闭串行端口连接
            return

        while True:
            if ser.in_waiting > 0:
                line = ser.readline().decode('utf-8').strip()
                if "Temperature is:" in line and args.temperature:
                    temperature = float(line.split(":")[1].strip().split(" ")[0])
                    print(f"Temperature: {temperature}")
                    break
                elif "Sensor Value:" in line and args.light:
                    light_value = int(line.split(":")[1].strip())
                    print(f"Light sensor value: {light_value}")
                    break
            time.sleep(interval)
    except serial.SerialException:
        print(f"Failed to open port {port}.")
        list_serial_ports()
        return
    finally:
        ser.close()

if __name__ == '__main__':
    main()
