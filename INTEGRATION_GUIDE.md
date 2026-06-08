# Z_PDF_Unlocker - GitHub & Docker Hub 对接部署指南

为了实现代码提交后**自动构建 Docker 镜像并推送至 Docker Hub**，以及在发布新版本标签（Tag）时**自动编译生成 Windows 单文件绿色版 EXE 并创建 GitHub Release**，我们为您配置了完整的 GitHub Actions 工作流。

以下是为您准备的一键对接配置步骤：

---

## 1. 准备工作

### A. 获取 Docker Hub 访问令牌 (Personal Access Token)
为了让 GitHub Actions 有权限推送镜像，不建议直接使用 Docker Hub 的登录密码，而是建议使用安全性更高的 Token：
1. 登录 [Docker Hub](https://hub.docker.com/)。
2. 点击右上角头像，选择 **Account Settings** (账号设置)。
3. 在左侧菜单栏选择 **Security** -> **Personal Access Tokens** (个人访问令牌)。
4. 点击 **New Access Token**，填写描述（例如 `github-actions-token`），权限选择 **Read & Write** (读写权限)，然后点击 **Generate**。
5. **复制生成的 Token 字符串**（注意：它只会出现一次，关闭窗口后将无法再次查看）。

---

## 2. 在 GitHub 仓库中配置 Secrets

您需要将您的 Docker Hub 账号及刚刚生成的 Token 保存到 GitHub 的加密 Secrets 中：
1. 打开您的 GitHub 仓库页面。
2. 点击顶部的 **Settings** (设置) 选项卡。
3. 在左侧菜单栏找到 **Security**，点击展开 **Secrets and variables** -> **Actions**。
4. 在 **Repository secrets** 区域，点击 **New repository secret** 按钮，分别添加以下两个机密：

| 秘密名称 (Secret Name) | 填入的值 (Secret Value) | 说明 |
| :--- | :--- | :--- |
| `DOCKER_USERNAME` | `您的 Docker Hub 用户名` | 例如 `newbee` |
| `DOCKER_TOKEN` | `刚刚复制的 Docker Hub Access Token` | 用于安全登录 Docker Hub 的令牌 |

> [!NOTE]
> 编译 Windows 可执行程序并自动创建 Release 所需的 `GITHUB_TOKEN` 是由 GitHub 内部自动注入的，**无需**您手动创建或配置。

---

## 3. 工作流运行触发逻辑

您在工作区中看到的 `.github/workflows/deploy.yml` 脚本会自动根据不同的代码提交动作执行不同的构建逻辑：

### 流程一：日常开发提交 (Push to `main` branch)
* **动作**：向 `main` 分支进行 `git push` 或合并 PR。
* **效果**：自动构建 Docker 镜像，并推送到 Docker Hub 仓库，标签为 `latest`。
  * 例如：`docker pull 您的用户名/z-pdf-unlocker:latest`

### 流程二：发布版本版本标签 (Push tag `v*`)
* **动作**：在本地给代码打上符合 `v*` 规则的版本标签并推送到 GitHub。
  ```bash
  git tag v1.0.0
  git push origin v1.0.0
  ```
* **效果**（自动双重构建流程）：
  1. **构建 Docker 镜像**：自动以 `v1.0.0` 和 `1.0` 等版本号命名标签，并推送至 Docker Hub。
  2. **构建 Windows 可执行程序**：在 GitHub 的 Windows 虚拟运行环境中，使用 PyInstaller 编译生成 `Z_PDF_Unlocker.exe` 单文件绿色版本。
  3. **自动发布 Release**：编译完成后，GitHub Actions 会在您的仓库中自动新建一个名为 `Z_PDF_Unlocker Release v1.0.0` 的 **Release 版本发布页面**，并将编译好的 `Z_PDF_Unlocker.exe` 自动上传为该 Release 的下载附件，供所有人直接下载使用！

---

## 4. 远程拉取与部署说明

对接成功后，您或您的局域网用户可以直接通过 Docker Hub 进行极简拉取部署：

```bash
# 1. 从您的 Docker Hub 仓库拉取最新镜像
docker pull 您的用户名/z-pdf-unlocker:latest

# 2. 启动容器运行解密服务 (映射 53535 端口)
docker run -d -p 53535:53535 --name z_pdf_unlocker 您的用户名/z-pdf-unlocker:latest
```
此时，镜像会以默认的安全局域网共享模式运行，在局域网内任意手机或电脑浏览器输入 `http://您的主机IP:53535` 即可打开访问验证页面，输入密码后便可流畅使用。
