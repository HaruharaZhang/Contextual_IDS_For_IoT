import serial
import serial.tools.list_ports
import time

def list_serial_ports():
    """ 列出系统中所有可用的串行端口 """
    ports = serial.tools.list_ports.comports()
    available_ports = []
    for port, desc, hwid in sorted(ports):
        print(f"{port}: {desc} ({hwid})")
        available_ports.append(port)
    return available_ports

def send_command(ser, command):
    """ 发送命令到Arduino """
    ser.write((command + "\n").encode())  # 发送命令字符串，后跟换行符
    print("Sent:", command)
    time.sleep(0.5)  # 稍等一会，确保Arduino有时间处理命令

def main():
    print("Available serial ports:")
    ports = list_serial_ports()
    
    if not ports:
        print("No serial ports found. Check your connections and drivers.")
        return
    
    # 让用户选择串行端口
    selected_port = input("Enter the port you'd like to use (e.g., COM3, /dev/ttyUSB0): ")
    
    # 尝试打开选定的串行端口
    try:
        ser = serial.Serial(selected_port, 9600, timeout=1)
        print(f"Connected to {selected_port}")

        try:
            while True:
                # 循环发送不同的命令
                print("Setting NORMAL state...")
                send_command(ser, "NORMAL")
                time.sleep(5)

                print("Setting WARNING state...")
                send_command(ser, "WARNING")
                time.sleep(5)

                print("Setting ALERT state...")
                send_command(ser, "ALERT")
                time.sleep(5)

        except KeyboardInterrupt:
            print("Program stopped by user.")
        finally:
            ser.close()  # 确保串行连接在程序结束时被关闭
            print("Serial connection closed.")

    except serial.SerialException:
        print(f"Failed to connect to {selected_port}. Please check your port name and try again.")

if __name__ == "__main__":
    main()
