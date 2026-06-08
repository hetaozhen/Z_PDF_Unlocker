# 使用官方轻量级 Python 镜像
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量，防止 Python 生成 .pyc 文件以及启用缓冲输出
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 移除 build-essential 等不必要的编译工具，因为我们依赖的库都有预编译的 wheel 包

# 复制依赖定义并安装
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目所有文件
COPY . .

# 暴露运行端口 (默认 53535)
EXPOSE 53535

# 容器启动命令：默认以局域网/公网可访问的模式启动，且不自动弹起浏览器
CMD ["python", "app.py", "--host", "0.0.0.0", "--port", "53535", "--no-browser"]
