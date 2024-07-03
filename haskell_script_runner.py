import subprocess
import argparse
import os

def compile_haskell(program_name):
    hs_file = f"Haskell/{program_name}.hs"
    output_executable = f"Haskell/{program_name}"
    # 确保源文件存在
    if not os.path.exists(hs_file):
        print(f"Error: Haskell source file '{hs_file}' not found.")
        return False
    # 编译 Haskell 程序
    compile_command = ["ghc", "-o", output_executable, hs_file]
    result = subprocess.run(compile_command, capture_output=True, text=True)
    if result.returncode == 0:
        print("Compilation successful.")
        return True
    else:
        print("Compilation failed:", result.stderr)
        return False

def call_haskell(program_name, device, state):
    executable_path = f"Haskell/{program_name}"
    if not os.path.exists(executable_path):
        print(f"Executable '{executable_path}' not found, attempting to compile...")
        if not compile_haskell(program_name):
            return "Compilation failed, cannot execute Haskell program."
    result = subprocess.run([executable_path, device, state], capture_output=True, text=True)
    return result.stdout

def main():
    parser = argparse.ArgumentParser(description='Compile and call a Haskell program with specified arguments.')
    parser.add_argument('-n', '--name', type=str, help='Name of the Haskell program (without .hs extension)', required=True)
    parser.add_argument('-d', '--device', type=str, help='Device argument for the Haskell program', required=True)
    parser.add_argument('-s', '--state', type=str, help='State argument for the Haskell program', required=True)

    args = parser.parse_args()

    # Example usage with command line arguments
    print(f"Calling Haskell program '{args.name}' with device '{args.device}' and state '{args.state}'")
    output = call_haskell(args.name, args.device, args.state)
    print(output)

if __name__ == "__main__":
    main()
