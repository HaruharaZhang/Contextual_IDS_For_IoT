import subprocess
import argparse
import os

def check_prolog_script(program_name):
    pl_file = f"Prolog/{program_name}.pl"
    # 确保源文件存在
    if not os.path.exists(pl_file):
        print(f"Error: Prolog source file '{pl_file}' not found.")
        return False
    return True

def call_prolog(program_name, bulb, switch, socket, voltage, sensor):
    pl_file = f"Prolog/{program_name}.pl"
    if not os.path.exists(pl_file):
        print(f"Prolog script '{pl_file}' not found.")
        return "Prolog script not found, cannot execute."
    # 构建 Prolog 命令
    prolog_command = ["swipl", "-s", pl_file, "-g", f"is_valid_state({bulb}, {switch}, {socket}, {voltage}, {sensor}),halt.", "-t", "halt"]
    result = subprocess.run(prolog_command, capture_output=True, text=True)
    return result.stdout

def main():
    parser = argparse.ArgumentParser(description='Call a Prolog script with specified arguments.')
    parser.add_argument('-n', '--name', type=str, help='Name of the Prolog script (without .pl extension)', required=True)
    parser.add_argument('-b', '--bulb', type=str, help='Bulb state (bulb_on or bulb_off)', required=True)
    parser.add_argument('-sw', '--switch', type=str, help='Switch state (switch_pressed or switch_not_pressed)', required=True)
    parser.add_argument('-so', '--socket', type=str, help='Socket state (socket_on or socket_off)', required=True)
    parser.add_argument('-v', '--voltage', type=str, help='Voltage state (high_voltage or low_voltage)', required=True)
    parser.add_argument('-se', '--sensor', type=str, help='Sensor state (sensor_high or sensor_low)', required=True)

    args = parser.parse_args()

    # Example usage with command line arguments
    print(f"Calling Prolog script '{args.name}' with state: Bulb='{args.bulb}', Switch='{args.switch}', Socket='{args.socket}', Voltage='{args.voltage}', Sensor='{args.sensor}'")
    output = call_prolog(args.name, args.bulb, args.switch, args.socket, args.voltage, args.sensor)
    print(output)

if __name__ == "__main__":
    main()
