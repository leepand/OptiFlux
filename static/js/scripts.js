// static/js/scripts.js
// 显示指定的功能模块
function showSection(sectionId) {
    // 隐藏所有内容区域
    document.querySelectorAll('.content-section').forEach(section => {
        section.style.display = 'none';
    });

    // 显示选中的内容区域
    const selectedSection = document.getElementById(`${sectionId}Section`);
    if (selectedSection) {
        selectedSection.style.display = 'block';
    }

    // 更新侧边栏的选中状态
    document.querySelectorAll('.sidebar .nav-link').forEach(link => {
        link.classList.remove('active');
    });

    // 查找 onclick 属性中包含 sectionId 的链接
    const targetLink = document.querySelector(`.sidebar .nav-link[onclick*="${sectionId}"]`);
    if (targetLink) {
        targetLink.classList.add('active');
    } else {
        console.error(`Sidebar link for section "${sectionId}" not found.`);
    }

    // 如果是 Model Versions 模块，默认加载 dev 环境的 model_name 列表
    if (sectionId === 'modelVersions') {
        const envSelect = document.getElementById('modelVersionsEnvSelect');
        if (envSelect) {
            const defaultEnv = envSelect.value; // 获取当前选中的环境
            loadModelNames(defaultEnv);  // 加载默认环境的 model_name 列表
        }
    }
    
    if (sectionId === 'operationLogs') {
        loadOperationLogs();
    }
    
    
}

// 初始化显示 Deploy 模块
showSection('deploy');
let currentPage = 1; // 当前页码
const perPage = 10; // 每页显示的条目数

// 加载某个环境下的 model_name 列表
function loadModelNames(env, page = 1) {
    const modelNamesList = document.getElementById('modelNamesList');
    modelNamesList.innerHTML = '<div class="text-center"><i class="bi bi-arrow-repeat spinner"></i> Loading model names...</div>';

    fetch(`/model_names?env=${env}&page=${page}&per_page=${perPage}`)
        .then(response => response.json())
        .then(result => {
            if (result.status === 'success') {
                let modelNamesHTML = '';
                result.model_names.forEach(model => {
                    modelNamesHTML += `
                        <div class="card mb-3">
                            <div class="card-body">
                                <h5 class="card-title">${model.model_name}</h5>
                                <div class="row">
                                    <div class="col-md-6">
                                        <p class="card-text">
                                            <strong>Version Count:</strong> ${model.version_count}
                                        </p>
                                        <p class="card-text">
                                            <strong>Max Version:</strong> ${model.max_version}
                                        </p>
                                        <p class="card-text">
                                            <strong>Total Size:</strong> ${(model.total_size / 1024 / 1024).toFixed(2)} MB
                                        </p>
                                        <p class="card-text">
                                            <strong>Latest Timestamp:</strong> ${model.latest_timestamp}
                                        </p>
                                    </div>
                                    <div class="col-md-6">
                                        <p class="card-text">
                                            <strong>Serving Version:</strong> ${model.serving_version || 'None'}
                                        </p>
                                        ${model.serving_version ? `
                                            <p class="card-text">
                                                <strong>Recomserver Ports:</strong>
                                                ${model.recomserver.map(recom => `
                                                    <span class="badge ${recom.status === 'Running' ? 'bg-success' : 'bg-danger'} me-1">
                                                        ${recom.port} (${recom.status === 'Running' ? 'Running' : 'Error'})
                                                    </span>
                                                `).join('')}
                                            </p>
                                            <p class="card-text">
                                                <strong>Rewardserver Ports:</strong>
                                                ${model.rewardserver.map(reward => `
                                                    <span class="badge ${reward.status === 'Running' ? 'bg-success' : 'bg-danger'} me-1">
                                                        ${reward.port} (${reward.status === 'Running' ? 'Running' : 'Error'})
                                                    </span>
                                                `).join('')}
                                            </p>
                                        ` : ''}
                                    </div>
                                </div>
                                <div class="d-flex justify-content-end gap-2 mt-3">
                                    <button class="btn btn-sm btn-primary" onclick="loadModelVersions('${env}', '${model.model_name}')">
                                        <i class="bi bi-eye me-1"></i>View Versions
                                    </button>
                                    <button class="btn btn-sm btn-info" onclick="showConfigManagement('${env}', '${model.model_name}')">
                                        <i class="bi bi-gear me-1"></i>Manage Config
                                    </button>
                                </div>
                            </div>
                        </div>
                    `;
                });
                modelNamesList.innerHTML = modelNamesHTML;
            } else {
                modelNamesList.innerHTML = '<div class="text-danger">Failed to load model names. Please try again later.</div>';
            }
        })
        .catch(error => {
            console.error("Error loading model names:", error);
            modelNamesList.innerHTML = '<div class="text-danger">An error occurred. Please try again later.</div>';
        });
}

async function loadModelNames22(env, page = 1) {
    currentPage = page; // 更新当前页码
    const modelNamesList = document.getElementById('modelNamesList');
    const pagination = document.getElementById('pagination');
    if (!modelNamesList || !pagination) {
        console.error("Model names list or pagination not found");
        return;
    }

    // 显示加载状态
    modelNamesList.innerHTML = '<div class="text-center"><i class="bi bi-arrow-repeat spinner"></i> Loading model names...</div>';
    pagination.innerHTML = '';

    try {
        const response = await fetch(`/model_names?env=${env}&page=${page}&per_page=${perPage}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const result = await response.json();
        console.log("Server response:", result); // 调试信息

        if (result.status === 'success') {
            // 清空之前的列表
            modelNamesList.innerHTML = '';

            // 动态生成 model_name 列表
            if (result.model_names.length === 0) {
                modelNamesList.innerHTML = '<div class="text-muted">No model names found.</div>';
            } else {
                result.model_names.forEach(model => {
                    const modelNameItem = document.createElement('div');
                    modelNameItem.className = 'card mb-3';
                    modelNameItem.innerHTML = `
                        <div class="card-body">
                            <h5 class="card-title">${model.model_name}</h5>
                            <div class="row">
                                <div class="col-md-6">
                                    <p class="card-text">
                                        <strong>Version Count:</strong> ${model.version_count}
                                    </p>
                                    <p class="card-text">
                                        <strong>Max Version:</strong> ${model.max_version}
                                    </p>
                                    <p class="card-text">
                                        <strong>Total Size:</strong> ${(model.total_size / 1024 / 1024).toFixed(2)} MB
                                    </p>
                                    <p class="card-text">
                                        <strong>Latest Timestamp:</strong> ${model.latest_timestamp}
                                    </p>
                                </div>
                                <div class="col-md-6">
                                    <p class="card-text">
                                        <strong>Recomserver Port:</strong> ${model.recomserver_port}
                                    </p>
                                    <p class="card-text">
                                        <strong>Recomserver Status:</strong> 
                                        <span class="badge ${model.recomserver_status === 'Running' ? 'bg-success' : 'bg-danger'}">
                                            ${model.recomserver_status}
                                        </span>
                                    </p>
                                    <p class="card-text">
                                        <strong>Rewardserver Port:</strong> ${model.rewardserver_port}
                                    </p>
                                    <p class="card-text">
                                        <strong>Rewardserver Status:</strong> 
                                        <span class="badge ${model.rewardserver_status === 'Running' ? 'bg-success' : 'bg-danger'}">
                                            ${model.rewardserver_status}
                                        </span>
                                    </p>
                                </div>
                            </div>
                            <div class="d-flex justify-content-end gap-2 mt-3">
                                <button class="btn btn-sm btn-primary" onclick="loadModelVersions('${env}', '${model.model_name}')">
                                    <i class="bi bi-eye me-1"></i>View Versions
                                </button>
                                <button class="btn btn-sm btn-info" onclick="showConfigManagement('${env}', '${model.model_name}')">
                                    <i class="bi bi-gear me-1"></i>Manage Config
                                </button>
                            </div>
                        </div>
                    `;
                    modelNamesList.appendChild(modelNameItem);
                });
            }

            // 动态生成分页按钮
            const totalPages = Math.ceil(result.total / perPage);
            let paginationHTML = '';
            if (totalPages > 1) {
                // 上一页按钮
                paginationHTML += `
                    <li class="page-item ${page === 1 ? 'disabled' : ''}">
                        <a class="page-link" href="#" onclick="loadModelNames('${env}', ${page - 1})">Previous</a>
                    </li>
                `;

                // 页码按钮
                for (let i = 1; i <= totalPages; i++) {
                    paginationHTML += `
                        <li class="page-item ${i === page ? 'active' : ''}">
                            <a class="page-link" href="#" onclick="loadModelNames('${env}', ${i})">${i}</a>
                        </li>
                    `;
                }

                // 下一页按钮
                paginationHTML += `
                    <li class="page-item ${page === totalPages ? 'disabled' : ''}">
                        <a class="page-link" href="#" onclick="loadModelNames('${env}', ${page + 1})">Next</a>
                    </li>
                `;
            }
            pagination.innerHTML = paginationHTML;
            console.log("Pagination HTML:", paginationHTML); // 调试信息
        } else {
            console.error("Failed to load model names:", result.message);
            modelNamesList.innerHTML = '<div class="text-danger">Failed to load model names. Please try again later.</div>';
        }
    } catch (error) {
        console.error("Error loading model names:", error);
        modelNamesList.innerHTML = '<div class="text-danger">An error occurred. Please try again later.</div>';
    }
}

// 显示 model_name 列表，隐藏 model_versions 列表
function showModelNames22() {
    const modelNamesList = document.getElementById('modelNamesList');
    const modelVersionsList = document.getElementById('modelVersionsList');
    const pagination = document.getElementById('pagination'); // 获取分页控件
    const envSelect = document.getElementById('modelVersionsEnvSelect');

    if (modelNamesList && modelVersionsList && pagination && envSelect) {
        // 显示 model_name 列表和分页控件，隐藏 model_versions 列表
        modelNamesList.style.display = 'block';
        pagination.style.display = 'flex'; // 使用 flex 布局确保样式正确
        modelVersionsList.style.display = 'none';

        // 启用环境选择框
        envSelect.disabled = false;

        // 重新加载当前页的 model_name 列表
        const env = envSelect.value;
        loadModelNames(env, currentPage);
    }
}

/**
 * 显示右上角 Toast 通知
 * @param {string} icon - 图标类型（success, error, warning, info, question）
 * @param {string} title - 提示标题
 * @param {number} [timer=3000] - 自动关闭时间（毫秒）
 */
function showToast(icon, title, timer = 3000) {
    Swal.fire({
        icon: icon,
        title: title,
        toast: true, // 启用 Toast 模式
        position: 'top-end', // 固定在右上角
        showConfirmButton: false, // 不显示确认按钮
        timer: timer, // 自动关闭时间
    });
}

async function restartServices(env, modelName, modelVersion) {
    // 显示加载状态
    const loading = document.getElementById('loading');
    loading.style.display = 'block';

    try {
        // 调用后端接口
        const response = await fetch('/restart_services', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                env: env,
                model_name: modelName,
                model_version: modelVersion,
            }),
        });

        const result = await response.json();

        if (result.status === 'success') {
            // 显示成功 Toast
            showToast('success', 'Services restarted successfully!');

            // 重新加载模型版本数据
            loadModelVersions(env, modelName);
            // 刷新服务状态
            checkServiceStatus(env, modelName, modelVersion);
        } else {
            // 显示错误 Toast
            showToast('error', result.message || 'Failed to restart services.');
            // 重新加载模型版本数据
            loadModelVersions(env, modelName);
            // 刷新服务状态
            checkServiceStatus(env, modelName, modelVersion);
        }
    } catch (error) {
        // 显示错误 Toast
        showToast('error', 'An error occurred. Please try again later.');
        // 重新加载模型版本数据
            loadModelVersions(env, modelName);
            // 刷新服务状态
            checkServiceStatus(env, modelName, modelVersion);
    } finally {
        // 隐藏加载状态
        loading.style.display = 'none';
    }
}

// 重启服务
async function restartVersion(env, modelName, modelVersion) {
    try {
        const response = await fetch('/restart_services', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                env: env,
                model_name: modelName,
                model_version: modelVersion,
            }),
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const result = await response.json();
        if (result.status === 'success') {
            // 显示成功提示
            Swal.fire({
                icon: 'success',
                title: 'Success',
                text: 'Services restarted successfully!',
                showConfirmButton: false,
                timer: 1500
            });

            // 刷新服务状态
            checkServiceStatus(env, modelName, modelVersion);
        } else {
            console.error("Failed to restart services:", result.message);
            Swal.fire({
                icon: 'error',
                title: 'Error',
                text: result.message,
            });
        }
    } catch (error) {
        console.error("Error restarting services:", error);
        Swal.fire({
            icon: 'error',
            title: 'Error',
            text: 'An error occurred while restarting services.',
        });
    }
}

// 检查服务状态
async function checkServiceStatus(env, modelName, modelVersion) {
    try {
        const response = await fetch(`/check_service_status?env=${env}&model_name=${modelName}&model_version=${modelVersion}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const result = await response.json();

        if (result.status === 'success') {
            // 更新页面上的服务状态
            updateServiceStatus(result.recom_status, result.reward_status);
        } else {
            console.error("Failed to check service status:", result.message);
        }
    } catch (error) {
        console.error("Error checking service status:", error);
    }
}

// 更新服务状态显示
function updateServiceStatus(recomStatus, rewardStatus) {
    const versionsContent = document.getElementById('versionsContent');
    if (versionsContent) {
        // 更新 recomserver 状态
        for (const [port, isRunning] of Object.entries(recomStatus)) {
            const statusElement = document.getElementById(`recom-status-${port}`);
            if (statusElement) {
                statusElement.className = isRunning ? 'badge bg-success' : 'badge bg-danger';
                statusElement.innerText = isRunning ? 'Running' : 'Stopped';
            }
        }

        // 更新 rewardserver 状态
        for (const [port, isRunning] of Object.entries(rewardStatus)) {
            const statusElement = document.getElementById(`reward-status-${port}`);
            if (statusElement) {
                statusElement.className = isRunning ? 'badge bg-success' : 'badge bg-danger';
                statusElement.innerText = isRunning ? 'Running' : 'Stopped';
            }
        }
    }
}

// 页面加载时检查服务状态
window.onload = function () {
    const env = document.getElementById('modelVersionsEnvSelect').value;
    const modelName = document.querySelector('.card-title').innerText; // 获取当前模型名称
    const modelVersion = document.querySelector('.card-subtitle').innerText; // 获取当前版本
    checkServiceStatus(env, modelName, modelVersion);
};


// 重启版本
async function restartVersion2(env, modelName, modelVersion) {
    try {
        const response = await fetch(`/restart_version?env=${env}&model_name=${modelName}&model_version=${modelVersion}`, {
            method: 'POST'
        });
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const result = await response.json();

        if (result.status === 'success') {
            // 重新加载版本列表
            loadModelVersions(env, modelName);
        } else {
            console.error("Failed to restart version:", result.message);
            alert("Failed to restart version. Please try again later.");
        }
    } catch (error) {
        console.error("Error restarting version:", error);
        alert("An error occurred. Please try again later.");
    }
}


// 其他 JavaScript 代码保持不变...

let currentLogFile = null;  // 当前选中的日志文件

// 动态切换文件或文件夹上传
document.querySelectorAll('input[name="uploadType"]').forEach(input => {
    input.addEventListener('change', function () {
        if (this.value === 'file') {
            document.getElementById('fileUploadSection').style.display = 'block';
            document.getElementById('folderUploadSection').style.display = 'none';
            document.getElementById('codeFile').setAttribute('required', true);  // 添加required
            document.getElementById('codeFolder').removeAttribute('required');  // 移除required
        } else {
            document.getElementById('fileUploadSection').style.display = 'none';
            document.getElementById('folderUploadSection').style.display = 'block';
            document.getElementById('codeFile').removeAttribute('required');  // 移除required
            document.getElementById('codeFolder').setAttribute('required', true);  // 添加required
        }
    });
});

// 表单提交
document.getElementById('deployForm').addEventListener('submit', async function (event) {
    event.preventDefault();  // 阻止表单默认提交行为

    // 清空之前的提示信息
    const resultDiv = document.getElementById('deployResult');
    resultDiv.innerHTML = '<div class="text-center"><i class="bi bi-arrow-repeat spinner"></i> Deploying...</div>';

    // 禁用提交按钮
    const submitButton = document.querySelector('#deployForm button[type="submit"]');
    submitButton.disabled = true;

    const formData = new FormData();
    formData.append('env', document.getElementById('envSelect').value);
    formData.append('model_name', document.getElementById('modelName').value);
    formData.append('model_version', document.getElementById('modelVersion').value);
    formData.append('uploadType', document.querySelector('input[name="uploadType"]:checked').value);

    const uploadType = document.querySelector('input[name="uploadType"]:checked').value;
    if (uploadType === 'file') {
        const file = document.getElementById('codeFile').files[0];
        if (!file) {
            alert("Please select a file to upload.");
            submitButton.disabled = false;  // 启用提交按钮
            return;
        }
        formData.append('file', file);
    } else {
        const files = document.getElementById('codeFolder').files;
        if (files.length === 0) {
            alert("Please select a folder to upload.");
            submitButton.disabled = false;  // 启用提交按钮
            return;
        }
        for (let i = 0; i < files.length; i++) {
            formData.append('folder', files[i]);
        }
    }

    try {
        const response = await fetch('/deploy', {
            method: 'POST',
            body: formData
        });
        const result = await response.json();

        if (result.status === 'success') {
            resultDiv.innerHTML = `<div class="alert alert-success">${result.message}</div>`;
        } else {
            resultDiv.innerHTML = `<div class="alert alert-danger">${result.message}</div>`;
        }
    } catch (error) {
        console.error('Error during deployment:', error);
        resultDiv.innerHTML = '<div class="alert alert-danger">An error occurred. Please try again later.</div>';
    } finally {
        submitButton.disabled = false;  // 启用提交按钮
        resultDiv.scrollIntoView({ behavior: 'smooth', block: 'end' });  // 滚动到提示信息
    }
});

// 加载日志文件列表
async function loadLogFiles() {
    try {
        const response = await fetch('/log_files');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const result = await response.json();
        if (result.status === 'success') {
            const logFiles = document.getElementById('logFiles');
            logFiles.innerHTML = result.log_files.map(file => `
                <div class="log-file-item p-3 border rounded mb-2">
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <strong>${file.name}</strong>
                            <div class="text-muted small">
                                <span>Updated: ${file.modified_time}</span> |
                                <span>Size: ${file.size}</span>
                            </div>
                        </div>
                        <button class="btn btn-sm btn-outline-primary" onclick="selectLogFile('${file.name}')">
                            <i class="bi bi-file-earmark-text me-2"></i>View
                        </button>
                    </div>
                </div>
            `).join('');
        } else {
            console.error("Failed to load log files:", result.message);
        }
    } catch (error) {
        console.error("Error loading log files:", error);
    }
}

async function loadLogFiles2() {
    const logFiles = document.getElementById('logFiles');
    logFiles.innerHTML = '<div class="text-center"><i class="bi bi-arrow-repeat"></i> Loading...</div>';
    try {
        const response = await fetch('/log_files');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const result = await response.json();
        if (result.status === 'success') {
            logFiles.innerHTML = result.log_files.map(file => `
                <div class="log-file-item p-3 border rounded mb-2">
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <strong>${file.name}</strong>
                            <div class="text-muted small">
                                <span>Updated: ${file.modified_time}</span> |
                                <span>Size: ${file.size}</span>
                            </div>
                        </div>
                        <button class="btn btn-sm btn-outline-primary" onclick="selectLogFile('${file.name}')">
                            <i class="bi bi-file-earmark-text me-2"></i>View
                        </button>
                    </div>
                </div>
            `).join('');
        } else {
            console.error("Failed to load log files:", result.message);
        }
    } catch (error) {
        console.error("Error loading log files:", error);
    }
}

// 点击板块时刷新数据
function refreshLogFiles() {
    loadLogFiles2();  // 调用加载函数
    console.log("Log files refreshed!");
}

// 绑定点击事件
document.getElementById('refreshLogsButton').addEventListener('click', refreshLogFiles);

// 初始化加载
window.onload = loadLogFiles;

// 选择日志文件
function selectLogFile(fileName) {
    currentLogFile = fileName;  // 更新当前选中的日志文件

    // 显示 Log Content 模块
    const logContentCard = document.getElementById('logContentCard');
    logContentCard.style.display = 'block';

    // 显示当前查看的日志文件名
    const currentLogFileElement = document.getElementById('currentLogFile');
    currentLogFileElement.innerText = fileName;

    loadLogContent();  // 加载日志内容
}

// 加载日志内容

// 加载日志内容（修复版）
async function loadLogContent22() {
    if (!currentLogFile) return;

    try {
        const lines = document.getElementById('logLines').value;
        const response = await fetch(`/log_content?file=${currentLogFile}&lines=${lines}`);
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        const result = await response.json();

        if (result.status === 'success') {
            const logContentSection = document.getElementById('logContent');
            logContentSection.innerHTML = `
                <div class="d-flex gap-2 align-items-center mb-3 p-2 bg-light rounded">
                    <!-- 返回按钮 (替换为关闭功能) -->
                    <button class="btn btn-sm btn-outline-secondary" onclick="hideLogContent()">
                        <i class="bi bi-x-lg"></i>
                    </button>
                    
                    <!-- 刷新按钮 -->
                    <button class="btn btn-sm btn-primary" onclick="loadLogContent()" title="刷新日志">
                        <i class="bi bi-arrow-clockwise"></i>
                    </button>
                    
                    <!-- 复制按钮 -->
                    <button class="btn btn-sm btn-success" onclick="copyContent()" title="复制内容">
                        <i class="bi bi-clipboard"></i>
                    </button>
                </div>
                
                <!-- 日志内容区域 -->
                <pre class="p-3 bg-white rounded border" style="overflow: auto; max-height: 70vh;">
                    ${result.content}
                </pre>
            `;
        } else {
            console.error("Failed to load log content:", result.message);
        }
    } catch (error) {
        console.error("Error loading log content:", error);
    }
}


async function loadLogContent() {
    if (!currentLogFile) {
        return;  // 如果没有选中日志文件，直接返回
    }

    try {
        const lines = document.getElementById('logLines').value;  // 获取用户输入的行数
        const response = await fetch(`/log_content?file=${currentLogFile}&lines=${lines}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const result = await response.json();
        if (result.status === 'success') {
            const logContent = document.getElementById('logContent');
            logContent.innerText = result.content;
        } else {
            console.error("Failed to load log content:", result.message);
        }
    } catch (error) {
        console.error("Error loading log content:", error);
    }
}

// 监听 Number of Lines 输入框的变化
document.getElementById('logLines').addEventListener('change', () => {
    if (currentLogFile) {
        loadLogContent();  // 重新加载日志内容
    }
});

// 显示 Model Versions 模块并加载默认环境的信息
function showModelVersionsSection() {
    console.log("Model Versions section clicked");  // 调试信息

    // 调用 showSection 函数来切换界面
    showSection('modelVersions');

    // 显示 Model Versions 模块
    const modelVersionsSection = document.getElementById('modelVersionsSection');
    if (modelVersionsSection) {
        modelVersionsSection.style.display = 'block';
        console.log("Model Versions section displayed");  // 调试信息

        // 确保 DOM 元素加载完成后再调用 loadModelVersions
        setTimeout(() => {
            loadModelVersions();
        }, 0);  // 延迟 0 毫秒，确保 DOM 更新
    } else {
        console.error("Model Versions section not found");  // 调试信息
    }
}


// 隐藏 Log Content 模块
function hideLogContent() {
    const logContentCard = document.getElementById('logContentCard');
    logContentCard.style.display = 'none';
}

// 每隔5秒刷新一次日志文件列表
setInterval(loadLogFiles, 5000);


let currentPath = '';  // 当前路径
let currentModelName = '';  // 当前模型名称
let currentModelVersion = '';  // 当前模型版本

// 加载某个 model_name 下的版本列表
// 显示 Model Versions 列表
function loadModelNames(env, page = 1) {
    const modelNamesList = document.getElementById('modelNamesList');
    modelNamesList.innerHTML = '<div class="text-center"><i class="bi bi-arrow-repeat spinner"></i> Loading model names...</div>';

    fetch(`/model_names?env=${env}&page=${page}&per_page=${perPage}`)
        .then(response => response.json())
        .then(result => {
            if (result.status === 'success') {
                let modelNamesHTML = '';
                result.model_names.forEach(model => {
                    modelNamesHTML += `
                        <div class="card mb-3">
                            <div class="card-body">
                                <h5 class="card-title">${model.model_name}</h5>
                                <div class="row">
                                    <div class="col-md-6">
                                        <p class="card-text">
                                            <strong>Version Count:</strong> ${model.version_count}
                                        </p>
                                        <p class="card-text">
                                            <strong>Max Version:</strong> ${model.max_version}
                                        </p>
                                        <p class="card-text">
                                            <strong>Total Size:</strong> ${(model.total_size / 1024 / 1024).toFixed(2)} MB
                                        </p>
                                        <p class="card-text">
                                            <strong>Latest Timestamp:</strong> ${model.latest_timestamp}
                                        </p>
                                    </div>
                                    <div class="col-md-6">
                                        <p class="card-text">
                                            <strong>Serving Version:</strong> ${model.serving_version || 'None'}
                                        </p>
                                        ${model.serving_version ? `
                                            <p class="card-text">
                                                <strong>Recomserver Ports:</strong>
                                                ${model.recomserver.map(recom => `
                                                    <span class="badge ${recom.status === 'Running' ? 'bg-success' : 'bg-danger'} me-1">
                                                        ${recom.port} (${recom.status === 'Running' ? 'Running' : 'Error'})
                                                    </span>
                                                `).join('')}
                                            </p>
                                            <p class="card-text">
                                                <strong>Rewardserver Ports:</strong>
                                                ${model.rewardserver.map(reward => `
                                                    <span class="badge ${reward.status === 'Running' ? 'bg-success' : 'bg-danger'} me-1">
                                                        ${reward.port} (${reward.status === 'Running' ? 'Running' : 'Error'})
                                                    </span>
                                                `).join('')}
                                            </p>
                                        ` : ''}
                                    </div>
                                </div>
                                <div class="d-flex justify-content-end gap-2 mt-3">
                                    <button class="btn btn-sm btn-primary" onclick="loadModelVersions('${env}', '${model.model_name}')">
                                        <i class="bi bi-eye me-1"></i>View Versions
                                    </button>
                                    <button class="btn btn-sm btn-info" onclick="showConfigManagement('${env}', '${model.model_name}')">
                                        <i class="bi bi-gear me-1"></i>Manage Config
                                    </button>
                                </div>
                            </div>
                        </div>
                    `;
                });
                modelNamesList.innerHTML = modelNamesHTML;

                // 生成分页按钮
                const totalPages = Math.ceil(result.total / perPage);
                let paginationHTML = '';
                if (totalPages > 1) {
                    // 上一页按钮
                    paginationHTML += `
                        <li class="page-item ${page === 1 ? 'disabled' : ''}">
                            <a class="page-link" href="#" onclick="loadModelNames('${env}', ${page - 1})">Previous</a>
                        </li>
                    `;

                    // 页码按钮
                    for (let i = 1; i <= totalPages; i++) {
                        paginationHTML += `
                            <li class="page-item ${i === page ? 'active' : ''}">
                                <a class="page-link" href="#" onclick="loadModelNames('${env}', ${i})">${i}</a>
                            </li>
                        `;
                    }

                    // 下一页按钮
                    paginationHTML += `
                        <li class="page-item ${page === totalPages ? 'disabled' : ''}">
                            <a class="page-link" href="#" onclick="loadModelNames('${env}', ${page + 1})">Next</a>
                        </li>
                    `;
                }
                document.getElementById('pagination').innerHTML = paginationHTML;
            } else {
                modelNamesList.innerHTML = '<div class="text-danger">Failed to load model names. Please try again later.</div>';
            }
        })
        .catch(error => {
            console.error("Error loading model names:", error);
            modelNamesList.innerHTML = '<div class="text-danger">An error occurred. Please try again later.</div>';
        });
}
// 返回 Model Names 列表
function showModelNames() {
    const modelNamesList = document.getElementById('modelNamesList');
    const modelVersionsList = document.getElementById('modelVersionsList');
    const pagination = document.getElementById('pagination');
    const envSelect = document.getElementById('modelVersionsEnvSelect');

    if (modelNamesList && modelVersionsList && pagination && envSelect) {
        // 显示模型列表和分页控件，隐藏版本列表
        modelNamesList.style.display = 'block';
        pagination.style.display = 'flex';
        modelVersionsList.style.display = 'none';

        // 启用环境选择框
        envSelect.disabled = false;

        // 重新加载模型列表
        const env = envSelect.value;
        loadModelNames(env, currentPage);
    }
}

function showModelNames23() {
    const modelNamesList = document.getElementById('modelNamesList');
    const modelVersionsList = document.getElementById('modelVersionsList');
    const pagination = document.getElementById('pagination');

    if (modelNamesList && modelVersionsList && pagination) {
        // 显示模型列表和分页控件，隐藏版本列表
        modelNamesList.style.display = 'block';
        pagination.style.display = 'flex';
        modelVersionsList.style.display = 'none';

        // 重新加载模型列表
        const env = document.getElementById('modelVersionsEnvSelect').value;
        loadModelNames(env, currentPage);
    }
}

function loadModelVersions(env, modelName) {
    const modelVersionsList = document.getElementById('versionsContent');
    modelVersionsList.innerHTML = '<div class="text-center"><i class="bi bi-arrow-repeat spinner"></i> Loading model versions...</div>';

    // 禁用环境选择框
    const envSelect = document.getElementById('modelVersionsEnvSelect');
    if (envSelect) {
        envSelect.disabled = true;
    }

    fetch(`/model_versions?env=${env}&model_name=${modelName}`)
        .then(response => response.json())
        .then(result => {
            if (result.status === 'success') {
                let versionsHTML = '';
                result.model_versions.forEach(version => {
                    if (version.is_serving) {
                        // 当前服役版本，展示详细信息
                        versionsHTML += `
                            <div class="card mb-3 border-primary">
                                <div class="card-body">
                                    <h5 class="card-title">
                                        ${version.model_name} - ${version.model_version}
                                        <span class="badge bg-primary ms-2">Serving</span>
                                    </h5>
                                    <p class="card-text">
                                        <small class="text-muted">Last Updated: ${new Date(version.timestamp * 1000).toLocaleString()}</small>
                                    </p>
                                    <p class="card-text">
                                        <small class="text-muted">Total Size: ${(version.size / 1024 / 1024).toFixed(2)} MB</small>
                                    </p>
                                    <div class="mt-3">
                                        <h6>Service Status</h6>
                                        <ul class="list-group">
                                            ${version.recomserver.map(recom => `
                                                <li class="list-group-item">
                                                    <strong>Recomserver Port:</strong> ${recom.port}
                                                    <span class="badge ${recom.status === 'Running' ? 'bg-success' : 'bg-danger'} float-end">
                                                        ${recom.status === 'Running' ? 'Running' : 'Error'}
                                                    </span>
                                                </li>
                                            `).join('')}
                                            ${version.rewardserver.map(reward => `
                                                <li class="list-group-item">
                                                    <strong>Rewardserver Port:</strong> ${reward.port}
                                                    <span class="badge ${reward.status === 'Running' ? 'bg-success' : 'bg-danger'} float-end">
                                                        ${reward.status === 'Running' ? 'Running' : 'Error'}
                                                    </span>
                                                </li>
                                            `).join('')}
                                        </ul>
                                    </div>
                                    <div class="d-flex justify-content-end gap-2 mt-3">
                                        <button class="btn btn-sm btn-warning" onclick="restartServices('${env}', '${version.model_name}', '${version.model_version}')">
                                            <i class="bi bi-arrow-repeat me-1"></i>Restart
                                        </button>
                                        <button class="btn btn-sm btn-primary" onclick="loadModelFiles('${env}', '${version.model_name}', '${version.model_version}')">
                                            <i class="bi bi-folder me-1"></i>View Codes
                                        </button>
                                    </div>
                                </div>
                            </div>
                        `;
                    } else {
                        // 其他版本，展示基础信息并保留 Restart 和 View Codes 按钮
                        versionsHTML += `
                            <div class="card mb-2">
                                <div class="card-body">
                                    <h5 class="card-title">
                                        ${version.model_name} - ${version.model_version}
                                    </h5>
                                    <p class="card-text">
                                        <small class="text-muted">Last Updated: ${new Date(version.timestamp * 1000).toLocaleString()}</small>
                                    </p>
                                    <p class="card-text">
                                        <small class="text-muted">Total Size: ${(version.size / 1024 / 1024).toFixed(2)} MB</small>
                                    </p>
                                    <div class="d-flex justify-content-end gap-2 mt-3">
                                        <button class="btn btn-sm btn-warning" onclick="restartServices('${env}', '${version.model_name}', '${version.model_version}')">
                                            <i class="bi bi-arrow-repeat me-1"></i>Restart
                                        </button>
                                        <button class="btn btn-sm btn-primary" onclick="loadModelFiles('${env}', '${version.model_name}', '${version.model_version}')">
                                            <i class="bi bi-folder me-1"></i>View Codes
                                        </button>
                                    </div>
                                </div>
                            </div>
                        `;
                    }
                });
                modelVersionsList.innerHTML = versionsHTML;

                // 显示 Model Versions 列表
                document.getElementById('modelVersionsList').style.display = 'block';
                document.getElementById('modelNamesList').style.display = 'none';
                document.getElementById('pagination').style.display = 'none';
            } else {
                modelVersionsList.innerHTML = '<div class="text-danger">Failed to load model versions. Please try again later.</div>';
            }
        })
        .catch(error => {
            console.error("Error loading model versions:", error);
            modelVersionsList.innerHTML = '<div class="text-danger">An error occurred. Please try again later.</div>';
        });
}

async function loadModelVersions22(env, modelName) {
    const modelNamesList = document.getElementById('modelNamesList');
    const modelVersionsList = document.getElementById('modelVersionsList');
    const pagination = document.getElementById('pagination');
    const envSelect = document.getElementById('modelVersionsEnvSelect');
    if (!modelNamesList || !modelVersionsList || !pagination || !envSelect) {
        console.error("Required elements not found");
        return;
    }

    // 隐藏 model_name 列表和分页控件，显示 model_versions 列表
    modelNamesList.style.display = 'none';
    pagination.style.display = 'none';
    modelVersionsList.style.display = 'block';

    // 禁用环境选择框
    envSelect.disabled = true;

    // 显示加载状态
    modelVersionsList.innerHTML = `
        <div class="d-flex justify-content-between align-items-center mb-3">
            <button class="btn btn-outline-secondary" onclick="showModelNames()">
                <i class="bi bi-arrow-left me-2"></i>Back to Model Names
            </button>
        </div>
        <div class="text-center"><i class="bi bi-arrow-repeat spinner"></i> Loading model versions...</div>
    `;

    try {
        const response = await fetch(`/model_versions?env=${env}&model_name=${modelName}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const result = await response.json();

        if (result.status === 'success') {
            // 清空之前的列表
            let versionsHTML = `
                <div class="d-flex justify-content-between align-items-center mb-3">
                    <button class="btn btn-outline-secondary" onclick="showModelNames()">
                        <i class="bi bi-arrow-left me-2"></i>Back to Model Names
                    </button>
                </div>
            `;

            // 动态生成 model_versions 列表
            if (result.model_versions.length === 0) {
                versionsHTML += '<div class="text-muted">No model versions found.</div>';
            } else {
                result.model_versions.forEach(v => {
                    versionsHTML += `
                        <div class="card mb-2 ${v.is_serving ? 'border-primary' : ''}">
                            <div class="card-body">
                                <h5 class="card-title">
                                    ${v.model_name} - ${v.model_version}
                                    ${v.is_serving ? '<span class="badge bg-primary ms-2">Serving</span>' : ''}
                                </h5>
                                <p class="card-text">
                                    <small class="text-muted">Last Updated: ${v.timestamp}</small>
                                </p>
                                <p class="card-text">
                                    <small class="text-muted">Total Size: ${(v.size / 1024 / 1024).toFixed(2)} MB</small>
                                </p>
                                <p class="card-text">
                                    <small class="text-muted">Recomserver Port: ${v.recomserver_port}</small>
                                </p>
                                <p class="card-text">
                                    <small class="text-muted">Rewardserver Port: ${v.rewardserver_port}</small>
                                </p>
                                <div class="d-flex justify-content-end gap-2">
                                    <button class="btn btn-sm btn-primary" onclick="loadModelFiles('${env}', '${v.model_name}', '${v.model_version}')">
                                        <i class="bi bi-folder me-1"></i>View Codes
                                    </button>
                                    <button class="btn btn-sm btn-warning" onclick="restartServices('${env}', '${v.model_name}', '${v.model_version}')">
                                        <i class="bi bi-arrow-repeat me-1"></i>Restart
                                    </button>
                                </div>
                            </div>
                        </div>
                    `;
                });
            }
            modelVersionsList.innerHTML = versionsHTML;
        } else {
            console.error("Failed to load model versions:", result.message);
            modelVersionsList.innerHTML = `
                <div class="d-flex justify-content-between align-items-center mb-3">
                    <button class="btn btn-outline-secondary" onclick="showModelNames()">
                        <i class="bi bi-arrow-left me-2"></i>Back to Model Names
                    </button>
                </div>
                <div class="text-danger">Failed to load model versions. Please try again later.</div>
            `;
        }
    } catch (error) {
        console.error("Error loading model versions:", error);
        modelVersionsList.innerHTML = `
            <div class="d-flex justify-content-between align-items-center mb-3">
                <button class="btn btn-outline-secondary" onclick="showModelNames()">
                    <i class="bi bi-arrow-left me-2"></i>Back to Model Names
                </button>
            </div>
            <div class="text-danger">An error occurred. Please try again later.</div>
        `;
    }
}

// 加载文件/目录列表
// 加载文件/目录列表
async function loadModelFiles(env, modelName, modelVersion, path = '') {
    currentModelName = modelName;
    currentModelVersion = modelVersion;
    currentPath = path;

    try {
        const response = await fetch(`/model_files?env=${env}&model_name=${modelName}&model_version=${modelVersion}&path=${path}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const result = await response.json();

        if (result.status === 'success') {
            const modelFilesList = document.getElementById('modelFilesList');
            modelFilesList.innerHTML = result.files.map(file => `
                <div class="card mb-2">
                    <div class="card-body d-flex justify-content-between align-items-center">
                        <div>
                            <h5 class="card-title">
                                ${file.name}
                                <span class="badge ${file.type === 'directory' ? 'bg-primary' : 'bg-secondary'}">
                                    ${file.type}
                                </span>
                            </h5>
                            <p class="card-text">
                                <small class="text-muted">Size: ${file.size} bytes</small>
                                <small class="text-muted"> | Last Modified: ${new Date(file.last_modified * 1000).toLocaleString()}</small>
                            </p>
                        </div>
                        <button class="btn btn-sm btn-primary" onclick="${file.type === 'directory' ? `enterDirectory('${file.name}')` : `viewFileContent('${file.name}')`}">
                            ${file.type === 'directory' ? 'Open' : 'View'}
                        </button>
                    </div>
                </div>
            `).join('');

            // 显示文件/目录列表
            document.getElementById('modelVersionsList').style.display = 'none';
            document.getElementById('modelFilesSection').style.display = 'block';
            document.getElementById('fileContentSection').style.display = 'none';

            // 动态显示/隐藏 Go Up 按钮
            const goUpButton = document.querySelector('#modelFilesSection .btn-outline-primary');
            if (currentPath === '') {
                // 如果当前路径是根目录，隐藏 Go Up 按钮
                goUpButton.style.display = 'none';
            } else {
                // 否则显示 Go Up 按钮
                goUpButton.style.display = 'inline-block';
            }
        } else {
            console.error("Failed to load model files:", result.message);
        }
    } catch (error) {
        console.error("Error loading model files:", error);
    }
}

// 进入目录
function enterDirectory(dirName) {
    currentPath = currentPath ? `${currentPath}/${dirName}` : dirName;
    const env = document.getElementById('modelVersionsEnvSelect').value;
    loadModelFiles(env, currentModelName, currentModelVersion, currentPath);
}

// 返回上一级目录
function goUpDirectory() {
    const pathParts = currentPath.split('/');
    pathParts.pop();
    currentPath = pathParts.join('/');
    const env = document.getElementById('modelVersionsEnvSelect').value;
    loadModelFiles(env, currentModelName, currentModelVersion, currentPath);
}


// 查看文件内容
async function viewFileContent(fileName) {
    const env = document.getElementById('modelVersionsEnvSelect').value;
    const filePath = currentPath ? `${currentPath}/${fileName}` : fileName;

    try {
        const response = await fetch(`/model_file_content?env=${env}&model_name=${currentModelName}&model_version=${currentModelVersion}&path=${filePath}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const result = await response.json();

        if (result.status === 'success') {
            // 显示文件内容
            const fileContentSection = document.getElementById('fileContentSection');
            fileContentSection.innerHTML = `
                <div class="d-flex justify-content-between align-items-center mb-3">
                    <button class="btn btn-outline-secondary" onclick="hideFileContent()">
                        <i class="bi bi-arrow-left me-2"></i>Back to Files
                    </button>
                    <button class="btn btn-outline-primary" onclick="copyContent()">
                        <i class="bi bi-clipboard me-2"></i>Copy
                    </button>
                </div>
                <pre id="fileContent">${result.content}</pre>
            `;
            document.getElementById('modelFilesSection').style.display = 'none';
            fileContentSection.style.display = 'block';
        } else {
            console.error("Failed to load file content:", result.message);
        }
    } catch (error) {
        console.error("Error loading file content:", error);
    }
}
async function viewFileContent22(fileName) {
    const env = document.getElementById('modelVersionsEnvSelect').value;
    const filePath = currentPath ? `${currentPath}/${fileName}` : fileName;

    try {
        const response = await fetch(`/model_file_content?env=${env}&model_name=${currentModelName}&model_version=${currentModelVersion}&path=${filePath}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const result = await response.json();

        if (result.status === 'success') {
            document.getElementById('fileContent').innerText = result.content;
            document.getElementById('modelFilesSection').style.display = 'none';
            document.getElementById('fileContentSection').style.display = 'block';
        } else {
            console.error("Failed to load file content:", result.message);
        }
    } catch (error) {
        console.error("Error loading file content:", error);
    }
}

// 隐藏文件内容
function hideFileContent() {
    document.getElementById('fileContentSection').style.display = 'none';
    document.getElementById('modelFilesSection').style.display = 'block';
}

// 显示 Model Versions 列表
function showModelVersions() {
    document.getElementById('modelFilesSection').style.display = 'none';
    document.getElementById('modelVersionsList').style.display = 'block';
}

let currentEnv = '';
//let currentModelName = '';
//let currentModelVersion = '';

// 显示配置管理界面
function showConfigManagement(env, modelName) {
    currentEnv = env;
    currentModelName = modelName;

    // 禁用 Environment 选择框
    document.getElementById('modelVersionsEnvSelect').disabled = true;

    // 隐藏分页条和 Model Names 列表
    document.getElementById('modelNamesList').style.display = 'none';
    document.getElementById('pagination').style.display = 'none';

    // 显示配置管理界面
    document.getElementById('configManagementSection').style.display = 'block';
    loadConfig();
}

// 隐藏配置管理界面
function hideConfigManagement() {
    // 启用 Environment 选择框
    document.getElementById('modelVersionsEnvSelect').disabled = false;

    // 显示分页条和 Model Names 列表
    document.getElementById('modelNamesList').style.display = 'block';
    document.getElementById('pagination').style.display = 'flex'; // 使用 flex 布局确保样式正确

    // 隐藏配置管理界面
    document.getElementById('configManagementSection').style.display = 'none';
}


let editor;

// 加载配置文件内容
async function loadConfig() {
    try {
        const response = await fetch(`/get_config?env=${currentEnv}&model_name=${currentModelName}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const result = await response.json();

        if (result.status === 'success') {
            const container = document.getElementById('jsoneditor');

            // 销毁已有的编辑器实例
            if (editor) {
                editor.destroy();
            }

            // 初始化 JSON 编辑器
            const options = {
                mode: 'view', // 初始为只读模式
                modes: ['view', 'code', 'tree'], // 允许切换模式
                onError: (err) => {
                    console.error('JSON Editor Error:', err);
                }
            };
            editor = new JSONEditor(container, options);
            editor.set(result.config);
        } else {
            console.error("Failed to load config:", result.message);
        }
    } catch (error) {
        console.error("Error loading config:", error);
    }
}

// 进入编辑模式
function editConfig() {
    if (editor) {
        editor.setMode('code'); // 切换到代码编辑模式
    }

    // 显示保存和取消按钮，隐藏编辑按钮
    document.getElementById('editConfigButton').style.display = 'none';
    document.getElementById('saveConfigButton').style.display = 'inline-block';
    document.getElementById('cancelEditButton').style.display = 'inline-block';
}

// 取消编辑
function cancelEdit() {
    if (editor) {
        editor.setMode('view'); // 切换回只读模式
    }

    // 显示编辑按钮，隐藏保存和取消按钮
    document.getElementById('editConfigButton').style.display = 'inline-block';
    document.getElementById('saveConfigButton').style.display = 'none';
    document.getElementById('cancelEditButton').style.display = 'none';

    // 重新加载配置文件内容
    loadConfig();
}

// 保存配置文件
async function saveConfig() {
    try {
        const newConfig = editor.get(); // 获取编辑器中的 JSON 数据
        const response = await fetch('/update_config', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                env: currentEnv,
                model_name: currentModelName,
                config: newConfig,
            }),
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const result = await response.json();
        if (result.status === 'success') {
            // 显示 Toast 提示
            //const toast = new bootstrap.Toast(document.getElementById('toast'));
            //toast.show();
            showToast('success', 'Config updated successfully!');

            cancelEdit();
            hideConfigManagement(); // 返回上一层
            loadModelNames(currentEnv, currentPage); // 刷新数据
        } else {
            console.error("Failed to update config:", result.message);
            showToast("error",result.message);
        }
    } catch (error) {
        console.error("Error updating config:", error);
        showToast("error","An error occurred while updating the config.");
    }
}


function copyContent() {
    const contentElement = document.querySelector('#logContent pre') || document.getElementById('fileContent');
    if (!contentElement) {
        showToast('error', 'No content to copy.');
        return;
    }
    
    const content = contentElement.innerText;
    
    
    // 兼容性处理
    if (navigator.clipboard) {
        // 使用现代 Clipboard API
        navigator.clipboard.writeText(content)
            .then(() => showToast('success', '内容已复制!'))
            .catch(err => {
                console.error('Clipboard API 错误:', err);
                fallbackCopy(content); // 降级方案
            });
    } else {
        // 旧浏览器使用 execCommand
        fallbackCopy(content);
    }
}

// 旧版复制方法
function fallbackCopy(text) {
    const textarea = document.createElement('textarea');
    textarea.value = text;
    textarea.style.position = 'fixed'; // 避免滚动
    document.body.appendChild(textarea);
    textarea.select();
    
    try {
        const success = document.execCommand('copy');
        if (success) {
            showToast('success', '内容已复制!');
        } else {
            showToast('error', '复制失败，请手动选择文本后按 Ctrl+C');
        }
    } catch (err) {
        console.error('execCommand 错误:', err);
        showToast('error', '复制失败，请手动选择文本后按 Ctrl+C');
    } finally {
        document.body.removeChild(textarea);
    }
}


// 确保文档加载完成后执行
// 确保在 DOM 加载后执行
document.addEventListener('DOMContentLoaded', function() {
    // 初始加载数据
    loadOperationLogs();
});

let currentLogPage = 1;
const logsPerPage = 10;

function loadOperationLogs(page = 1) {
    currentLogPage = page;
    
    // 获取 DOM 元素
    const tableBody = document.getElementById('tableBody');
    const table = document.getElementById('operationLogsTable');
    const pagination = document.getElementById('logsPagination');
    
    // 确保元素存在
    if (!tableBody || !table || !pagination) {
        console.error('必要的 DOM 元素不存在');
        return;
    }

    // 显示加载中状态
    tableBody.innerHTML = `
        <tr>
            <td colspan="4" class="text-center">
                <i class="bi bi-arrow-repeat spinner"></i> 加载中...
            </td>
        </tr>
    `;

    // 发送请求获取数据
    fetch(`/operation_records?page=${page}&per_page=${logsPerPage}`)
        .then(response => response.json())
        .then(result => {
            if (result.status === 'success') {
                // 生成表格内容
                const tableRows = result.logs.map(log => `
                    <tr>
                        <td>${log.id}</td>
                        <td>${log.action}</td>
                        <td>
                            <pre">
                                ${JSON.stringify(log.details, null, 2)}
                            </pre>
                        </td>
                        <td>${new Date(log.timestamp).toLocaleString()}</td>
                    </tr>
                `).join('');
                
                tableBody.innerHTML = tableRows;

                // 计算总页数
                const totalPages = Math.ceil(result.total / logsPerPage);
                
                // 生成分页按钮
                const pageButtons = [];
                for (let i = 1; i <= totalPages; i++) {
                    const isActive = i === currentLogPage;
                    pageButtons.push(`
                        <li class="page-item ${isActive ? 'active' : ''}">
                            <a class="page-link" href="#" onclick="loadOperationLogs(${i})">${i}</a>
                        </li>
                    `);
                }

                // 生成上下页按钮
                const prevDisabled = currentLogPage === 1;
                const nextDisabled = currentLogPage === totalPages;
                
                const paginationContent = `
                    <li class="page-item ${prevDisabled ? 'disabled' : ''}">
                        <a class="page-link" href="#" onclick="loadOperationLogs(${currentLogPage - 1})">
                            <i class="bi bi-arrow-left"></i> Previous
                        </a>
                    </li>
                    ${pageButtons.join('')}
                    <li class="page-item ${nextDisabled ? 'disabled' : ''}">
                        <a class="page-link" href="#" onclick="loadOperationLogs(${currentLogPage + 1})">
                            Next <i class="bi bi-arrow-right"></i>
                        </a>
                    </li>
                `;

                // 更新分页内容
                pagination.querySelector('ul').innerHTML = paginationContent;
            }
        })
        .catch(error => {
            console.error('加载操作日志失败:', error);
            tableBody.innerHTML = `
                <tr>
                    <td colspan="4" class="text-center text-danger">
                        <i class="bi bi-exclamation-triangle"></i> 加载失败，请稍后重试。
                    </td>
                </tr>
            `;
        });
}

document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.dropdown-item[href*="logout"]').forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            if (confirm('确认注销吗？')) {
                document.getElementById('logout-form').submit();
            }
        });
    });
});
