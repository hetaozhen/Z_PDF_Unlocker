# Z_PDF_Unlocker 🔒🔓

一个极速、极简、高隐私的本地 PDF 文件解锁/解密 Web 工具。支持通过浏览器上传**单个文件**、**多个文件**或**整个文件夹**，并在内存中完成快速解密后提供直接下载。

---

## ✨ 核心特性

1. **🔒 零磁盘留存 (内存化安全处理)**：
   * 所有上传的 PDF 文件读取、密码匹配、解密及 ZIP 打包流程均在服务器 **RAM 内存**（`io.BytesIO`）中进行。
   * **绝对不往磁盘写入任何临时文件**，在服务重启或关闭后不留下任何隐私痕迹。

2. **📂 智能多模式上传 & 目录过滤**：
   * 支持拖拽（Drag & Drop）或点击按钮上传：**单个文件**、**多个文件**、或**整个文件夹**。
   * 前端会自动深度遍历文件夹，**只提取并上传 `.pdf` 格式文件**，自动忽略并过滤掉其他任何无用格式。

3. **📦 双通道部署与分发**：
   * **本地直接启动**：提供 Windows `run.bat` 和 Linux/macOS `run.sh` 脚本，双击/运行即可一键搭建好本地环境并自动打开浏览器。
   * **Docker 极简部署**：支持一键运行容器，方便在群晖 NAS、家庭服务器、局域网等多种环境中共享。

---

## 🛠️ 本地运行指南

### 方式一：Windows 用户（双击一键运行）
直接在项目根目录下双击运行 [run.bat](file:///e:/Z_PDF_Unlocker/run.bat)。
> 脚本会自动检测 Python 环境，自动使用 `pip` 安装所需依赖（`Flask`, `pypdf`, `cryptography`），启动 Flask 服务，并自动调起您的默认浏览器打开 `http://127.0.0.1:53535`。

### 方式二：Linux / macOS 用户
在终端中进入项目目录，赋予执行权限并运行 [run.sh](file:///e:/Z_PDF_Unlocker/run.sh)：
```bash
chmod +x run.sh setup.sh
./run.sh
```

### 方式三：手动启动命令
如果您习惯手动管理 Python 环境：
```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 运行服务
python app.py
```

---

## 🐳 Docker 部署指南

项目提供了完整的容器化部署支持，您可以选择以下两种方式之一运行：

### 方式一：从 Docker Hub 拉取预构建镜像部署（推荐）
这种方式最省时，不需要克隆源码或在服务器本地构建。

#### 1. 使用 docker run 运行
```bash
docker run -d \
  -p 53535:53535 \
  --name z_pdf_unlocker \
  -e TZ=Asia/Shanghai \
  -e LAN_PASSWORD=your_secure_password \
  hetaozhen/z-pdf-unlocker:latest
```

#### 2. 使用 Docker Compose 运行
直接下载或复制 [docker-compose.yml](file:///e:/Z_PDF_Unlocker/docker-compose.yml)，然后在其目录下执行：
```bash
docker compose up -d
```

---

### 方式二：本地自行构建部署（适用于二次开发）
如果您修改了本地代码，想在本地打包镜像进行测试：

#### 1. 命令行构建运行
在项目根目录下执行：
```bash
# 构建本地镜像
docker build -t z-pdf-unlocker:local .

# 运行本地镜像
docker run -d -p 53535:53535 --name z_pdf_unlocker_local -e LAN_PASSWORD=your_secure_password z-pdf-unlocker:local
```

#### 2. 使用 Docker Compose 本地构建运行
将 `docker-compose.yml` 中的 `image:` 换成 `build: .`，然后运行：
```bash
docker compose up -d --build
```

