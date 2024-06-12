# 使用官方Python镜像作为基础镜像
FROM python:3.9

# 维护者信息
LABEL maintainer="your_email@example.com"

# 更新包列表并安装必要的包
RUN apt-get update && apt-get install -y \
    mariadb-server \
    sudo \
    nmap \
    iputils-ping \
    && rm -rf /var/lib/apt/lists/*

# 创建一个新的用户 mysqluser，并将其添加到sudoers文件中
RUN useradd -m mysqluser && echo 'mysqluser ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers

# 创建 /var/run/mysqld 目录并设置权限
RUN mkdir -p /var/run/mysqld && chown -R mysqluser:mysqluser /var/lib/mysql /var/run/mysqld

# 设置环境变量以防止MariaDB在启动时要求输入交互式密码
ENV MYSQL_ALLOW_EMPTY_PASSWORD yes

# 复制当前目录的内容到容器中的/app目录
COPY . /app

# 设置工作目录
WORKDIR /app

# 安装Python依赖包
RUN pip install --no-cache-dir -r requirements.txt

# 安装特定的Python模块
RUN pip install python-nmap prettytable pymysql

# 更改/app目录权限
RUN chown -R mysqluser:mysqluser /app

# 切换到 mysqluser 用户
USER mysqluser

# 启动MariaDB服务并保持容器运行
CMD ["mysqld"]
