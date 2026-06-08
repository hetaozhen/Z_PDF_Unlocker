# Z_PDF_Unlocker - 综合部署与 GitHub / Docker Hub 对接指南

为了实现代码提交后**自动构建 Docker 镜像并推送至 Docker Hub**，以及在发布新版本标签（Tag）时**自动编译生成 Windows 单文件绿色版 EXE 并创建 GitHub Release**，我们为您配置了完整的 GitHub Actions 工作流。

同时，为了方便您在本地、云服务器（如 CentOS）等不同环境下灵活部署，以下是为您整理的详细 Docker 部署指南与对接步骤。

---

## 1. Docker 部署指南 (Docker Deployment Guide)

项目已提供完整的 Docker 支持，您可以通过以下两种方式进行容器化部署：

### 方式一：从 Docker Hub 拉取预构建镜像部署（推荐，适用于 CentOS 等服务器）
这种方式**不需要**您在服务器上克隆源码或复制 `Dockerfile`，直接拉取我们在 Docker Hub 编译好的公共镜像即可，适合极速部署。

#### 1. 命令行一键运行
直接运行以下命令（请将 `your_secure_password` 替换为您自定义的页面访问密码）：
```bash
docker run -d \
  -p 53535:53535 \
  --name z_pdf_unlocker \
  -e TZ=Asia/Shanghai \
  -e LAN_PASSWORD=your_secure_password \
  hetaozhen/z-pdf-unlocker:latest
```

#### 2. 使用 Docker Compose 运行（推荐）
在服务器上新建任意目录，创建一个 [docker-compose.yml](file:///e:/Z_PDF_Unlocker/docker-compose.yml) 文件（内容如下）：
```yaml
version: '3.8'

services:
  pdf-unlocker:
    image: hetaozhen/z-pdf-unlocker:latest
    container_name: z_pdf_unlocker
    ports:
      - "53535:53535"
    restart: unless-stopped
    environment:
      - TZ=Asia/Shanghai
      - LAN_PASSWORD=your_secure_password # 设置您的页面访问密码
```
在该目录下执行以下命令即可启动：
```bash
docker compose up -d
```

---

### 方式二：本地自行构建并部署（适用于二次开发与本地调试）
如果您修改了本地代码，想要在本地通过 `Dockerfile` 打包成专属的容器进行测试：

#### 1. 命令行本地构建并运行
首先确保终端路径在项目根目录下（包含 `Dockerfile`）：
```bash
# 1. 本地构建 Docker 镜像
docker build -t z-pdf-unlocker:local .

# 2. 运行本地镜像（可通过 -e 注入自定义环境变量）
docker run -d \
  -p 53535:53535 \
  --name z_pdf_unlocker_local \
  -e LAN_PASSWORD=your_secure_password \
  z-pdf-unlocker:local
```

#### 2. 使用 Docker Compose 本地构建运行
如果您希望使用 `docker-compose` 指令直接在本地实时构建并运行，只需将 `docker-compose.yml` 中的 `image:` 替换为 `build:` 指向当前目录即可：
```yaml
version: '3.8'

services:
  pdf-unlocker:
    build: . # 修改为使用本地 Dockerfile 进行构建
    container_name: z_pdf_unlocker
    ports:
      - "53535:53535"
    restart: unless-stopped
    environment:
      - TZ=Asia/Shanghai
      - LAN_PASSWORD=your_secure_password
```
运行构建并启动：
```bash
docker compose up -d --build
```

---

## 2. GitHub & Docker Hub 自动化对接配置

### 步骤 A：获取 Docker Hub 访问令牌
1. 登录 [Docker Hub](https://hub.docker.com/)。
2. 点击右上角头像，选择 **Account Settings** (账号设置) -> **Security**。
3. 点击 **New Access Token**，填写描述（如 `github-actions`），权限选择 **Read & Write**，点击 **Generate**。
4. **复制生成的 Token 字符串**。

### 步骤 B：在 GitHub 仓库中配置 Secrets
1. 打开您的 GitHub 仓库页面，进入 **Settings** -> **Secrets and variables** -> **Actions**。
2. 点击 **New repository secret**，分别添加以下两个机密：

| 秘密名称 (Secret Name) | 填入的值 (Secret Value) |
| :--- | :--- |
| `DOCKER_USERNAME` | `您的 Docker Hub 用户名` (例如 `hetaozhen`) |
| `DOCKER_TOKEN` | `在步骤 A 中复制的 Access Token` |

---

## 3. 自动化流水线触发逻辑

配置好 Secrets 并提交 [.github/workflows/deploy.yml](file:///e:/Z_PDF_Unlocker/.github/workflows/deploy.yml) 工作流后：

1. **日常代码推送 (Push to `main`)**：
   * 自动构建 Docker 镜像并推送至 Docker Hub，标记为 `latest` 标签。
   * 服务器上运行 `docker compose pull` 即可无缝拉取最新版部署。

2. **版本发布标签 (Push tag `v*`)**：
   * 自动编译生成 Windows 单文件绿色版 `Z_PDF_Unlocker.exe`。
   * 自动在 GitHub 上创建 Release，并将 `.exe` 附件上传，供直接下载。
   * 同时推送带版本号的镜像至 Docker Hub（如 `hetaozhen/z-pdf-unlocker:v1.0.1`）。
