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

def parse_arguments():
    parser = argparse.ArgumentParser(description="Read temperature and light sensor values from a serial port.")
    parser.add_argument("-t", "--temperature", help="Read and return temperature value.", action="store_true")
    parser.add_argument("-l", "--light", help="Read and return light sensor value.", action="store_true")
    return parser.parse_args()

def main():
    args = parse_arguments()
    config = load_config()

    port = config.get('port')
    baudrate = config.getint('baudrate')
    interval = config.getfloat('interval')

    try:
        ser = serial.Serial(port, baudrate)
    except serial.SerialException:
        print(f"Failed to open port {port}.")
        list_serial_ports()
        return

    while True:
        if ser.in_waiting > 0:
            line = ser.readline().decode('utf-8').strip()
            if "Temperature is:" in line and args.temperature:
                temperature = float(line.split(":")[1].strip().split(" ")[0])
                print(f"Temperature: {temperature} Celsius")
                break
            elif "Sensor Value:" in line and args.light:
                light_value = int(line.split(":")[1].strip())
                print(f"Light sensor value: {light_value}")
                break
        time.sleep(interval)

if __name__ == '__main__':
    main()
