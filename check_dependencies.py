import sys
import pkg_resources
import subprocess 


def check_and_install_dependencies(config_path='Config/requirement.cfg'):
    dependencies = []
    with open(config_path, 'r') as file:
        for line in file:
            # 忽略注释和空行
            if line.strip() and not line.strip().startswith('#'):
                dependencies.append(line.strip())
    
    not_installed = []
    for package in dependencies:
        try:
            pkg_resources.get_distribution(package)
        except pkg_resources.DistributionNotFound:
            print(f"{package} is NOT installed.")
            not_installed.append(package)

    # 尝试安装未安装的依赖库
    for package in not_installed:
        try:
            print(f"Attempting to install {package}...")
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
            print(f"{package} has been successfully installed.")
        except subprocess.CalledProcessError:
            print(f"Failed to install {package}.")

    # 再次检查是否安装成功
    still_missing = []
    for package in not_installed:
        try:
            pkg_resources.get_distribution(package)
        except pkg_resources.DistributionNotFound:
            still_missing.append(package)

    if not still_missing:
        return "All required packages are installed."
    else:
        return f"Failed to install these packages: {', '.join(still_missing)}"

if __name__ == "__main__":
    result = check_and_install_dependencies()
    print(result)
