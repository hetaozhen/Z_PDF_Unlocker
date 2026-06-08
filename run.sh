#!/bin/bash

# ===================================================
#             Z_PDF_Unlocker Launcher
# ===================================================

# 检查虚拟环境是否存在
if [ ! -d ".venv" ]; then
    echo "[错误] 未检测到虚拟环境目录 (.venv)！"
    echo "请先运行设置脚本初始化环境: ./setup.sh"
    exit 1
fi

# 激活虚拟环境
source .venv/bin/activate

# 运行 Flask 服务，传递所有脚本接收到的参数
echo "正在启动 Z_PDF_Unlocker 服务..."
python3 app.py "$@"
