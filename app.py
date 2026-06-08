import os
import io
import uuid
import time
import zipfile
import threading
import sys
import webbrowser
import argparse
import socket
import pypdf
from flask import Flask, jsonify, request, send_file, render_template

# 跨平台非阻塞键盘输入读取
if sys.platform.startswith('win'):
    try:
        import msvcrt
    except ImportError:
        msvcrt = None
        
    def get_key_nonblocking():
        if msvcrt and msvcrt.kbhit():
            char = msvcrt.getwch()
            if char in ('\r', '\n'):
                return '\n'
            return char
        return None
else:
    import select
    try:
        import termios
        import tty
    except ImportError:
        termios = None
        tty = None
        
    def get_key_nonblocking():
        if termios is None or tty is None or not sys.stdin.isatty():
            return None
        try:
            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            try:
                tty.setraw(fd)
                rlist, _, _ = select.select([sys.stdin], [], [], 0)
                if rlist:
                    char = sys.stdin.read(1)
                    if char in ('\r', '\n'):
                        return '\n'
                    return char
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        except Exception:
            pass
        return None

# 适配 PyInstaller 单文件打包时的静态资源获取路径
def get_resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), relative_path)

static_dir = get_resource_path('static')
template_dir = get_resource_path('templates')
app = Flask(__name__, static_folder=static_dir, template_folder=template_dir)
app.secret_key = uuid.uuid4().hex

# 局域网访问密码 (仅在 Option 2 局域网共享模式下强制设置)
LAN_PASSWORD = None
FAILED_ATTEMPTS = 0
LOCK_UNTIL = 0.0

# 内存下载缓存，结构：{ download_id: { 'data': bytes, 'filename': str, 'mimetype': str, 'timestamp': float } }
DOWNLOAD_CACHE = {}

def cleanup_cache_loop():
    """后台垃圾回收线程：每隔 60 秒清理一次缓存，删除创建时间超过 5 分钟的文件对象"""
    while True:
        time.sleep(60)
        now = time.time()
        expired_keys = [k for k, v in DOWNLOAD_CACHE.items() if now - v['timestamp'] > 300]
        for k in expired_keys:
            DOWNLOAD_CACHE.pop(k, None)

# 启动后台守护线程
cleanup_thread = threading.Thread(target=cleanup_cache_loop, daemon=True)
cleanup_thread.start()

@app.route('/')
def index():
    is_local = request.remote_addr in ('127.0.0.1', '::1')
    
    # 局域网访问且未登录，提示验证输入密码
    if LAN_PASSWORD and not is_local:
        from flask import session
        if not session.get('authenticated'):
            return render_template('login.html')
            
    return render_template('index.html', is_local=is_local, mode="LAN" if LAN_PASSWORD else "LOCAL")

@app.route('/api/login', methods=['POST'])
def login():
    global FAILED_ATTEMPTS, LOCK_UNTIL
    now = time.time()
    if now < LOCK_UNTIL:
        remaining = int(LOCK_UNTIL - now)
        return jsonify({'success': False, 'error': f'尝试次数过多，请在 {remaining} 秒后再试。'}), 429
        
    data = request.get_json() or {}
    pwd = data.get('password', '')
    
    if pwd == LAN_PASSWORD:
        FAILED_ATTEMPTS = 0
        from flask import session
        session['authenticated'] = True
        return jsonify({'success': True})
    else:
        FAILED_ATTEMPTS += 1
        # 延迟防暴破
        time.sleep(1.0)
        if FAILED_ATTEMPTS >= 5:
            LOCK_UNTIL = time.time() + 30
            return jsonify({'success': False, 'error': '密码错误次数过多，锁定 30 秒。'}), 429
        return jsonify({'success': False, 'error': f'密码错误，还可尝试 {5 - FAILED_ATTEMPTS} 次。'})

@app.route('/favicon.ico')
def favicon():
    return send_file(get_resource_path('static/favicon.ico'), mimetype='image/x-icon')

@app.route('/api/unlock', methods=['POST'])
def unlock_files():
    password = request.form.get('password', '')
    uploaded_files = request.files.getlist('files')
    
    if not uploaded_files or len(uploaded_files) == 0 or uploaded_files[0].filename == '':
        return jsonify({'success': False, 'error': '未收到上传的文件'}), 400
        
    # 过滤出以 .pdf 结尾的文件
    pdf_files = [f for f in uploaded_files if f.filename.lower().endswith('.pdf')]
    
    if not pdf_files:
        return jsonify({'success': False, 'error': '未检测到任何 PDF 文件'}), 400
        
    # 情况 1：仅有 1 个 PDF 文件
    if len(pdf_files) == 1:
        file = pdf_files[0]
        filename = file.filename
        base_name = os.path.basename(filename)
        
        try:
            in_bytes = file.read()
            in_stream = io.BytesIO(in_bytes)
            reader = pypdf.PdfReader(in_stream)
            
            # 如果文件本身没有被加密，直接返回原文件流
            if not reader.is_encrypted:
                out_filename = base_name[:-4] + '_unlocked.pdf'
                download_id = str(uuid.uuid4())
                DOWNLOAD_CACHE[download_id] = {
                    'data': in_bytes,
                    'filename': out_filename,
                    'mimetype': 'application/pdf',
                    'timestamp': time.time()
                }
                return jsonify({
                    'success': True,
                    'download_url': f'/api/download/{download_id}',
                    'filename': out_filename
                })
                
            # 尝试解密
            status = reader.decrypt(password)
            if status == 0:
                return jsonify({'success': False, 'error': '密码错误，解密失败'}), 400
                
            # 写入解密后的文件
            writer = pypdf.PdfWriter()
            writer.append(reader)
            
            out_stream = io.BytesIO()
            writer.write(out_stream)
            out_bytes = out_stream.getvalue()
            
            out_filename = base_name[:-4] + '_unlocked.pdf'
            download_id = str(uuid.uuid4())
            DOWNLOAD_CACHE[download_id] = {
                'data': out_bytes,
                'filename': out_filename,
                'mimetype': 'application/pdf',
                'timestamp': time.time()
            }
            return jsonify({
                'success': True,
                'download_url': f'/api/download/{download_id}',
                'filename': out_filename
            })
            
        except Exception as e:
            return jsonify({'success': False, 'error': f'解密文件时出错: {str(e)}'}), 500
            
    # 情况 2：有多个 PDF 文件
    else:
        zip_buffer = io.BytesIO()
        success_files = []
        failed_files = []
        used_names = set()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for file in pdf_files:
                filename = file.filename
                base_name = os.path.basename(filename)
                
                # 重名防覆盖机制
                name_no_ext, ext = os.path.splitext(base_name)
                out_name = f"{name_no_ext}_unlocked{ext}"
                
                counter = 1
                temp_out_name = out_name
                while temp_out_name.lower() in used_names:
                    temp_out_name = f"{name_no_ext}_unlocked_{counter}{ext}"
                    counter += 1
                out_name = temp_out_name
                used_names.add(out_name.lower())
                
                try:
                    in_bytes = file.read()
                    in_stream = io.BytesIO(in_bytes)
                    reader = pypdf.PdfReader(in_stream)
                    
                    # 如果没有加密，直接写入 ZIP
                    if not reader.is_encrypted:
                        in_stream.seek(0)
                        zip_file.writestr(out_name, in_stream.read())
                        success_files.append(f"{filename} (未加密)")
                        continue
                        
                    status = reader.decrypt(password)
                    if status == 0:
                        failed_files.append((filename, '密码错误'))
                        continue
                        
                    writer = pypdf.PdfWriter()
                    writer.append(reader)
                    
                    out_stream = io.BytesIO()
                    writer.write(out_stream)
                    out_stream.seek(0)
                    
                    zip_file.writestr(out_name, out_stream.read())
                    success_files.append(filename)
                    
                except Exception as e:
                    failed_files.append((filename, str(e)))
            
            # 生成解密报告
            report_content = [
                "===================================================",
                "             Z_PDF_Unlocker - 批量处理报告",
                "===================================================\n",
                f"成功解锁文件数: {len(success_files)}",
                f"失败文件数: {len(failed_files)}\n"
            ]
            
            if success_files:
                report_content.append("--- 成功解锁列表 ---")
                for s in success_files:
                    report_content.append(f"[成功] {s}")
                report_content.append("")
                
            if failed_files:
                report_content.append("--- 失败列表 ---")
                for f, err in failed_files:
                    report_content.append(f"[失败] {f} (原因: {err})")
                report_content.append("")
                
            report_str = "\n".join(report_content)
            zip_file.writestr("decryption_report.txt", report_str)
            
        # 如果没有一个文件解密成功，直接返回错误
        if len(success_files) == 0:
            errors_summary = "; ".join([f"{f}: {err}" for f, err in failed_files])
            return jsonify({'success': False, 'error': f'全部文件解密失败。详情: {errors_summary}'}), 400
            
        zip_bytes = zip_buffer.getvalue()
        download_id = str(uuid.uuid4())
        DOWNLOAD_CACHE[download_id] = {
            'data': zip_bytes,
            'filename': 'unlocked_pdfs.zip',
            'mimetype': 'application/zip',
            'timestamp': time.time()
        }
        return jsonify({
            'success': True,
            'download_url': f'/api/download/{download_id}',
            'filename': 'unlocked_pdfs.zip'
        })

@app.route('/api/download/<download_id>', methods=['GET'])
def download_file(download_id):
    """
    通过 HTTP GET 请求下载解密好的文件。
    这种方式可以完美适配 IDM 等下载工具的多线程二次请求拦截，且文件依然保留在服务器内存中，绝不写盘。
    """
    file_info = DOWNLOAD_CACHE.get(download_id)
    if not file_info:
        return "该下载链接已失效或文件不存在，请重新提交解锁", 404
        
    return send_file(
        io.BytesIO(file_info['data']),
        mimetype=file_info['mimetype'],
        as_attachment=True,
        download_name=file_info['filename']
    )

@app.route('/api/shutdown', methods=['POST'])
def shutdown():
    """退出 EXE 服务 (仅限本机用户)"""
    is_local = request.remote_addr in ('127.0.0.1', '::1')
    if not is_local:
        return jsonify({'success': False, 'error': '无权进行此操作，仅限本机用户关闭服务。'}), 403
        
    def terminate():
        time.sleep(0.5)
        os._exit(0)
    threading.Thread(target=terminate).start()
    return jsonify({'success': True, 'message': '服务已关闭，您可以安全关闭此页面。'})

def is_port_in_use(port):
    """检测端口是否被占用 (通过尝试绑定 127.0.0.1 检测)"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('127.0.0.1', port))
            return False
        except socket.error:
            return True

def print_header():
    print("===================================================")
    print("              Z_PDF_Unlocker 运行模式选择")
    print("===================================================")

def determine_port(default_port=53535):
    """
    检查默认端口，如果被占用，停在界面中提示用户输入自定义端口并循环检测，直到端口可用。
    """
    if not is_port_in_use(default_port):
        return default_port
        
    print(f"[冲突] 默认端口 {default_port} 已被占用！")
    while True:
        try:
            user_input = input("请输入自定义端口 (建议在 10000 以上): ").strip()
            if not user_input:
                print(" 端口输入不能为空，请重新输入。")
                continue
            port = int(user_input)
            if port < 1024 or port > 65535:
                print(" 端口范围必须在 1024 到 65535 之间！请重新输入。")
                continue
            
            if is_port_in_use(port):
                print(f" [错误] 端口 {port} 仍被占用，请尝试其他端口。")
            else:
                print(f" [成功] 端口 {port} 可用！\n")
                return port
        except ValueError:
            print(" 请输入有效的数字作为端口号！")

def select_host_mode(timeout=5):
    """
    在控制台窗口提供 5 秒倒计时选择，支持局域网模式切换。
    """
    print(" [1] 仅本机访问 (推荐，默认安全选项)")
    print(" [2] 允许局域网设备访问 (允许其他手机/电脑访问)")
    print("===================================================")
    
    start_time = time.time()
    choice = ''
    last_seconds_left = -1
    
    while True:
        elapsed = time.time() - start_time
        seconds_left = max(0, int(timeout - elapsed))
        
        # 仅在剩余秒数变化时刷新输出
        if seconds_left != last_seconds_left:
            sys.stdout.write(f"\r请选择运行模式 [1 或 2，默认 1] (倒计时 {seconds_left} 秒): ")
            sys.stdout.flush()
            last_seconds_left = seconds_left
            
        # 监听键盘输入
        char = get_key_nonblocking()
        if char is not None:
            if char == '\n':
                if not choice:
                    choice = '1'
                break
            elif char in ('1', '2'):
                choice = char
                sys.stdout.write(choice + "\n")
                sys.stdout.flush()
                break
            
        # 检测超时
        if elapsed >= timeout:
            if not choice:
                choice = '1'
            sys.stdout.write(f"\n[提示] {timeout} 秒超时未选择，默认进入：[1] 仅本机访问\n")
            sys.stdout.flush()
            break
            
        time.sleep(0.05)
        
    if choice == '2':
        print("\n===================================================")
        print("              局域网共享模式安全设置")
        print("===================================================")
        global LAN_PASSWORD
        while True:
            pwd = input(" 请设置局域网访问密码 (最少 6 位): ").strip()
            if len(pwd) < 6:
                print("   [错误] 密码最少需要 6 位，请重新输入！")
                continue
            LAN_PASSWORD = pwd
            print("   [安全] 局域网访问密码设置成功！")
            break
        print("===================================================")
        print("[状态] 服务已启动，绑定 IP: 0.0.0.0 (局域网内可通过您的电脑 IP 访问)")
        return '0.0.0.0'
    else:
        print("[状态] 服务已启动，绑定 IP: 127.0.0.1 (仅限本机访问)")
        return '127.0.0.1'

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Z_PDF_Unlocker")
    parser.add_argument('--host', type=str, default=None, help='Host to bind')
    parser.add_argument('--port', type=int, default=None, help='Port to bind')
    parser.add_argument('--no-browser', action='store_true', help='Do not open browser')
    args = parser.parse_args()
    
    # 打印运行界面标题
    print_header()
    
    # 1. 确定可用的运行端口
    port = args.port
    if port is None:
        port = determine_port(53535)
    else:
        if is_port_in_use(port):
            print(f"[警告] 指定端口 {port} 似乎已被占用，运行可能会报错。")
            
    # 2. 确定绑定 Host 模式
    host = args.host
    if host is None:
        host = select_host_mode(timeout=5)
            
    # 3. 自动打开浏览器
    if not args.no_browser:
        def open_browser(p):
            time.sleep(1.0)
            target_host = '127.0.0.1' if host == '0.0.0.0' else host
            webbrowser.open(f"http://{target_host}:{p}")
            
        threading.Thread(target=open_browser, args=(port,), daemon=True).start()
        
    # 4. 关闭 debug=True 保证生产运行干净稳定
    app.run(host=host, port=port, debug=False)
