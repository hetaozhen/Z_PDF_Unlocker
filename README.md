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

3. **🚀 适配 IDM 等下载器拦截**：
   * 采用 “先 POST 上传解密、后分配专属 GET 凭证流式下载” 的两阶段策略。
   * 完美解决 Internet Download Manager (IDM) 等多线程下载工具二次请求导致接口报 `400 Bad Request` 的痛点。

4. **🎨 极具现代感的 Web 界面**：
   * 采用**磨砂毛玻璃质感 (Glassmorphism)** 视觉设计，搭配舒适的暗黑模式。
   * 支持文件上传列表状态实时更新（待解密、解密中、成功 🔓、失败 ❌）。
   * 包含操作日志控制台，实时展示每一份文件的解锁状态。

5. **📦 双通道部署与分发**：
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

项目提供了完整的容器化支持，可以使用 Docker 极速构建与启动。

### 1. 本地构建并运行
```bash
# 构建镜像
docker build -t z-pdf-unlocker .

# 启动容器（将容器内 53535 端口映射至宿主机 53535 端口）
docker run -d -p 53535:53535 --name pdf_unlocker z-pdf-unlocker
```
运行后，在浏览器访问 `http://localhost:53535` 即可使用。

### 2. 通过 Docker Compose 部署
我们同样配置了 [docker-compose.yml](file:///e:/Z_PDF_Unlocker/docker-compose.yml)：
```bash
docker-compose up -d
```

---

## ⚙️ 排除文件配置 (Exclusions)

为了保证项目的整洁度与安全性，我们做好了完善的排除配置：

1. **Git 排除 ([.gitignore](file:///e:/Z_PDF_Unlocker/.gitignore))**：
   * 自动忽略 Python 的虚拟环境（`venv/`、`env/`）、打包产生的缓存中间件（`build/`）、生成的单个 Windows 绿色可执行程序（`dist/`）以及 `*.spec` 配置文件。
   * 避免将本地测试的敏感 PDF 文件误上传到公开的代码仓库。

2. **Docker 排除 ([.dockerignore](file:///e:/Z_PDF_Unlocker/.dockerignore))**：
   * 过滤掉所有的 `.git` 元数据和 `.github` 工作流。
   * **排除本地测试的所有 `*.pdf` 文件**，以防在构建公开镜像时，将您的私密 PDF 测试数据打包封存进镜像中，确保了镜像发布的安全性。

---

## 🚀 CI/CD 自动构建与发布

当您将代码推送至 GitHub 后：
1. **Docker 镜像自动推送**：GitHub Actions 会自动编译 Docker 镜像，在通过安全验证后将其自动推送至您的 **Docker Hub** 账号中。
2. **Windows 单文件版发布**：当您打上版本 Tag（如 `v1.0.0`）推送到 GitHub 时，Actions 会自动使用 PyInstaller 编译出一个免安装的 `Z_PDF_Unlocker.exe` 单文件绿色版本，并自动为您创建 GitHub Release，将该 `.exe` 作为资产附件上传，供您及其他用户直接下载。

> 具体的 GitHub 与 Docker Hub 的对接配置步骤，请参阅专用的 [对接部署指南](file:///e:/Z_PDF_Unlocker/INTEGRATION_GUIDE.md)。
