document.addEventListener('DOMContentLoaded', () => {
    // DOM 元素引用
    const dropzone = document.getElementById('dropzone');
    const inputSingle = document.getElementById('input-single');
    const inputMultiple = document.getElementById('input-multiple');
    const inputDirectory = document.getElementById('input-directory');
    
    const btnSelectSingle = document.getElementById('btn-select-single');
    const btnSelectMultiple = document.getElementById('btn-select-multiple');
    const btnSelectDirectory = document.getElementById('btn-select-directory');
    
    const queueCard = document.getElementById('queue-card');
    const fileList = document.getElementById('file-list');
    const fileCount = document.getElementById('file-count');
    const filterWarning = document.getElementById('filter-warning');
    const filterWarningText = document.getElementById('filter-warning-text');
    
    const passwordInput = document.getElementById('password-input');
    const togglePassword = document.getElementById('toggle-password');
    const eyeIcon = document.getElementById('eye-icon');
    
    const btnUnlockSubmit = document.getElementById('btn-unlock-submit');
    const btnClear = document.getElementById('btn-clear');
    const btnShutdown = document.getElementById('btn-shutdown');
    const toastContainer = document.getElementById('toast-container');

    // 内存中的待上传 PDF 文件队列
    let fileQueue = [];

    // ==========================================================================
    // 基础交互事件绑定 (按钮触发隐藏的文件输入框)
    // ==========================================================================
    btnSelectSingle.addEventListener('click', (e) => {
        e.stopPropagation();
        inputSingle.click();
    });
    
    btnSelectMultiple.addEventListener('click', (e) => {
        e.stopPropagation();
        inputMultiple.click();
    });
    
    btnSelectDirectory.addEventListener('click', (e) => {
        e.stopPropagation();
        inputDirectory.click();
    });

    // 文件选择改变事件监听
    inputSingle.addEventListener('change', (e) => handleFileSelection(e.target.files));
    inputMultiple.addEventListener('change', (e) => handleFileSelection(e.target.files));
    inputDirectory.addEventListener('change', (e) => handleFileSelection(e.target.files));

    // 密码明文/密文切换
    togglePassword.addEventListener('click', () => {
        const isPassword = passwordInput.type === 'password';
        passwordInput.type = isPassword ? 'text' : 'password';
        eyeIcon.setAttribute('data-lucide', isPassword ? 'eye-off' : 'eye');
        lucide.createIcons();
    });

    // ==========================================================================
    // 拖拽上传 (Drag & Drop) 事件监听
    // ==========================================================================
    ['dragenter', 'dragover'].forEach(eventName => {
        dropzone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropzone.classList.add('dragover');
        }, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropzone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropzone.classList.remove('dragover');
        }, false);
    });

    dropzone.addEventListener('drop', async (e) => {
        const dt = e.dataTransfer;
        const items = dt.items;
        
        if (items) {
            let filesList = [];
            let promises = [];
            
            // 遍历拖拽的项目并递归展开目录
            for (let i = 0; i < items.length; i++) {
                const item = items[i];
                if (item.kind === 'file') {
                    const entry = item.webkitGetAsEntry();
                    if (entry) {
                        promises.push(traverseFileTree(entry));
                    }
                }
            }
            
            const results = await Promise.all(promises);
            results.forEach(files => {
                filesList = filesList.concat(files);
            });
            
            handleFileSelection(filesList);
        } else {
            // 浏览器 fallback
            handleFileSelection(dt.files);
        }
    });

    // 递归读取文件夹目录树中的文件
    function traverseFileTree(entry) {
        return new Promise((resolve) => {
            let files = [];
            if (entry.isFile) {
                entry.file((file) => {
                    files.push(file);
                    resolve(files);
                });
            } else if (entry.isDirectory) {
                const dirReader = entry.createReader();
                
                // 读取文件夹下的所有项
                const readAllEntries = () => {
                    dirReader.readEntries(async (entries) => {
                        if (entries.length === 0) {
                            resolve(files);
                        } else {
                            let subPromises = [];
                            for (let i = 0; i < entries.length; i++) {
                                subPromises.push(traverseFileTree(entries[i]));
                            }
                            const results = await Promise.all(subPromises);
                            results.forEach(r => {
                                files = files.concat(r);
                            });
                            // 继续读（以防单次读取未读完）
                            readAllEntries();
                        }
                    });
                };
                readAllEntries();
            }
        });
    }

    // ==========================================================================
    // 文件队列处理与过滤核心逻辑
    // ==========================================================================
    function handleFileSelection(files) {
        if (!files || files.length === 0) return;
        
        let pdfCount = 0;
        let ignoredCount = 0;
        
        for (let i = 0; i < files.length; i++) {
            const file = files[i];
            
            // 过滤：仅接受以 .pdf 结尾的文件
            if (file.name.toLowerCase().endsWith('.pdf')) {
                // 防止重复添加同一个文件（以文件名+大小校验）
                const isDuplicate = fileQueue.some(item => item.name === file.name && item.size === file.size);
                if (!isDuplicate) {
                    fileQueue.push(file);
                    pdfCount++;
                }
            } else {
                ignoredCount++;
            }
        }
        
        // UI Toast 提示
        if (pdfCount > 0) {
            showToast(`成功导入 ${pdfCount} 个 PDF 文件`, 'success');
        }
        if (ignoredCount > 0) {
            showToast(`已自动忽略 ${ignoredCount} 个非 PDF 文件`, 'warning');
            filterWarning.classList.remove('hidden');
            filterWarningText.textContent = `已自动忽略本次选择中的 ${ignoredCount} 个非 PDF 格式文件。`;
        }
        
        renderQueue();
    }

    // 格式化文件大小
    function formatBytes(bytes, decimals = 2) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const dm = decimals < 0 ? 0 : decimals;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
    }

    function escapeHtml(str) {
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    // 渲染待解密队列列表
    function renderQueue() {
        fileList.innerHTML = '';
        
        if (fileQueue.length === 0) {
            queueCard.classList.add('hidden');
            btnUnlockSubmit.disabled = true;
            filterWarning.classList.add('hidden');
            return;
        }
        
        queueCard.classList.remove('hidden');
        fileCount.textContent = `${fileQueue.length} 个 PDF`;
        btnUnlockSubmit.disabled = false;
        
        fileQueue.forEach((file, index) => {
            const li = document.createElement('li');
            li.className = 'file-item';
            
            const safeName = escapeHtml(file.name);
            
            li.innerHTML = `
                <div class="file-info">
                    <div class="file-icon-wrapper">
                        <i data-lucide="file-text"></i>
                    </div>
                    <div class="file-details">
                        <span class="file-name" title="${safeName}">${safeName}</span>
                        <div class="file-meta">
                            <span>大小: ${formatBytes(file.size)}</span>
                        </div>
                    </div>
                </div>
                <div class="file-actions">
                    <button class="btn-remove-file" onclick="removeQueueItem(${index})" title="移除该文件">
                        <i data-lucide="x"></i>
                    </button>
                </div>
            `;
            fileList.appendChild(li);
        });
        
        lucide.createIcons();
    }

    // 移除队列中的单个文件
    window.removeQueueItem = function(index) {
        fileQueue.splice(index, 1);
        renderQueue();
        showToast('已移出队列', 'info');
    };

    // 清空队列
    btnClear.addEventListener('click', () => {
        fileQueue = [];
        // 清空 input 控件的值，使得同一个文件夹再次选择时依然能触发 change 事件
        inputSingle.value = '';
        inputMultiple.value = '';
        inputDirectory.value = '';
        renderQueue();
        showToast('队列已清空', 'info');
    });

    // ==========================================================================
    // 解密提交流与二进制下载
    // ==========================================================================
    btnUnlockSubmit.addEventListener('click', async () => {
        const password = passwordInput.value.trim();
        if (!password) {
            showToast('请输入解密密码！', 'error');
            passwordInput.focus();
            return;
        }

        if (fileQueue.length === 0) {
            showToast('队列为空，请先选择要解密的文件！', 'error');
            return;
        }

        // 按钮显示加载状态
        const originalText = btnUnlockSubmit.innerHTML;
        btnUnlockSubmit.disabled = true;
        btnUnlockSubmit.innerHTML = `<div class="spinner" style="width:16px;height:16px;border-width:1px;"></div> 正在处理并解密...`;
        
        showToast(`正在解密并打包 ${fileQueue.length} 个文件，请稍候...`, 'info');

        // 构建 FormData
        const formData = new FormData();
        formData.append('password', password);
        fileQueue.forEach(file => {
            formData.append('files', file);
        });

        try {
            const response = await fetch('/api/unlock', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();
            
            if (response.ok && data.success) {
                // 成功：通过后端分配的专属 GET 接口进行下载，完美适配 IDM 拦截
                const a = document.createElement('a');
                a.href = data.download_url;
                a.download = data.filename;
                document.body.appendChild(a);
                a.click();
                a.remove();
                showToast('解密成功！已自动为您启动下载。', 'success');
            } else {
                // 失败：显示错误消息
                showToast(data.error || '解密失败，请检查密码！', 'error');
            }
        } catch (err) {
            console.error(err);
            showToast('请求超时或本地服务响应异常', 'error');
        } finally {
            // 恢复按钮状态
            btnUnlockSubmit.disabled = false;
            btnUnlockSubmit.innerHTML = originalText;
        }
    });

    // ==========================================================================
    // 关闭服务与退出程序
    // ==========================================================================
    if (btnShutdown) {
        btnShutdown.addEventListener('click', async () => {
            if (confirm('确认要关闭 Z_PDF_Unlocker 本地服务并退出程序吗？')) {
                showToast('正在向本地服务发送关闭指令...', 'info');
                try {
                    const response = await fetch('/api/shutdown', {
                        method: 'POST'
                    });
                    const data = await response.json();
                    if (data.success) {
                        showToast('服务已成功关闭，正在尝试关闭此标签页...', 'success');
                        setTimeout(() => {
                            window.close();
                            // 浏览器策略阻止关闭时的回退处理
                            document.body.innerHTML = `
                                <div style="
                                    display: flex;
                                    flex-direction: column;
                                    justify-content: center;
                                    align-items: center;
                                    height: 100vh;
                                    text-align: center;
                                    font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                                    background-color: #090d16;
                                    color: #f3f4f6;
                                    padding: 20px;
                                ">
                                    <div style="
                                        width: 64px;
                                        height: 64px;
                                        border-radius: 50%;
                                        background-color: rgba(239, 68, 68, 0.1);
                                        border: 1px solid rgba(239, 68, 68, 0.2);
                                        display: flex;
                                        align-items: center;
                                        justify-content: center;
                                        color: #ef4444;
                                        margin-bottom: 24px;
                                        font-size: 32px;
                                    ">✕</div>
                                    <h1 style="font-size: 24px; font-weight: 700; margin-bottom: 8px;">服务已成功关闭</h1>
                                    <p style="color: #9ca3af; font-size: 14px;">本地服务进程已正常退出。您现在可以安全地关闭此浏览器标签页。</p>
                                </div>
                            `;
                        }, 1000);
                    }
                } catch (err) {
                    console.error(err);
                    showToast('关闭服务请求失败或服务已处于关闭状态。', 'error');
                }
            }
        });
    }

    // ==========================================================================
    // Toast 提示信息系统
    // ==========================================================================
    function showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        
        let iconName = 'info';
        if (type === 'success') iconName = 'check-circle';
        if (type === 'error') iconName = 'alert-triangle';
        if (type === 'warning') iconName = 'info';
        
        toast.innerHTML = `
            <i data-lucide="${iconName}" class="toast-icon"></i>
            <span>${message}</span>
        `;
        
        toastContainer.appendChild(toast);
        
        // 重新渲染 Toast 中的图标
        lucide.createIcons({
            attrs: {
                class: 'toast-icon'
            }
        });
        
        setTimeout(() => {
            toast.classList.add('toast-fade-out');
            setTimeout(() => {
                toast.remove();
            }, 300);
        }, 4000);
    }

    window.showToast = showToast;
    
    // 页面初始载入时，渲染所有的 Lucide 图标
    lucide.createIcons();
});
