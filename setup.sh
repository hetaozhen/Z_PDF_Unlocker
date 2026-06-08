#!/bin/bash

# ===================================================
#             Z_PDF_Unlocker Linux Setup Script
# ===================================================

set -e

echo "==================================================="
echo "           Z_PDF_Unlocker Linux Setup"
echo "==================================================="
echo

# 1. 检查 Python 3
if ! command -v python3 &>/dev/null; then
    echo "[错误] 未检测到 Python 3，请先安装 Python 3。"
    echo "Ubuntu/Debian: sudo apt update && sudo apt install python3 python3-pip python3-venv"
    echo "CentOS/RHEL: sudo dnf install python3 python3-pip"
    exit 1
fi

echo "[1/3] 检测到 Python 3: $(python3 --version)"

# 2. 创建虚拟环境
if [ ! -d ".venv" ]; then
    echo "[2/3] 正在创建 Python 虚拟环境 (.venv)..."
    python3 -m venv .venv
else
    echo "[2/3] 虚拟环境 (.venv) 已存在，跳过创建。"
fi

# 3. 安装依赖
echo "[3/3] 正在激活虚拟环境并安装/升级依赖..."
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo
echo "==================================================="
echo "[OK] 环境配置成功！"
echo "您可以通过以下方式运行服务："
echo "  - 前台运行交互选择: ./run.sh"
echo "  - 局域网无浏览器后台运行: ./run.sh --host 0.0.0.0 --port 53535 --no-browser"
echo "==================================================="
chmod +x run.sh || true
