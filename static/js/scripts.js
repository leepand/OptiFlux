// static/js/scripts.js
// 显示指定的功能模块

// 创建登出确认弹窗
function createLogoutConfirm(onConfirm, onCancel) {
    // 容器元素
    const overlay = document.createElement('div');
    overlay.style = `
      position: fixed;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      background: rgba(0,0,0,0.4);
      display: flex;
      justify-content: center;
      align-items: center;
      z-index: 1000;
      animation: fadeIn 0.3s ease;
    `;
  
    // 弹窗主体
    const dialog = document.createElement('div');
    dialog.style = `
      background: #fff;
      padding: 24px;
      border-radius: 12px;
      box-shadow: 0 8px 32px rgba(0,0,0,0.2);
      width: 320px;
      transform: translateY(-20px);
      opacity: 0;
      animation: slideIn 0.3s ease forwards;
    `;
  
    // 标题
    const title = document.createElement('h3');
    title.textContent = '确认退出系统';
    title.style = `
      margin: 0 0 16px;
      font-size: 20px;
      color: #1f2937;
      font-weight: 600;
    `;
  
    // 内容
    const content = document.createElement('p');
    content.textContent = '您正在尝试安全退出当前账户，是否继续操作？';
    content.style = `
      margin: 0 0 24px;
      color: #4b5563;
      line-height: 1.5;
    `;
  
    // 按钮容器
    const btnGroup = document.createElement('div');
    btnGroup.style = `
      display: flex;
      gap: 12px;
      justify-content: flex-end;
    `;
  
    // 取消按钮
    const cancelBtn = document.createElement('button');
    cancelBtn.textContent = '取消';
    cancelBtn.style = `
      padding: 10px 20px;
      background: #f3f4f6;
      color: #4b5563;
      border: none;
      border-radius: 8px;
      cursor: pointer;
      transition: all 0.2s;
      font-weight: 500;
    `;
    cancelBtn.onmouseover = () => cancelBtn.style.background = '#e5e7eb';
    cancelBtn.onmouseout = () => cancelBtn.style.background = '#f3f4f6';
    cancelBtn.onclick = () => {
      overlay.remove();
      onCancel?.();
    };
  
    // 确认按钮
    const confirmBtn = document.createElement('button');
    confirmBtn.textContent = '确认退出';
    confirmBtn.style = `
      padding: 10px 20px;
      background: #ef4444;
      color: white;
      border: none;
      border-radius: 8px;
      cursor: pointer;
      transition: all 0.2s;
      font-weight: 500;
    `;
    confirmBtn.onmouseover = () => confirmBtn.style.background = '#dc2626';
    confirmBtn.onmouseout = () => confirmBtn.style.background = '#ef4444';
    confirmBtn.onclick = () => {
      overlay.remove();
      onConfirm?.();
    };
  
    // 组装元素
    btnGroup.append(cancelBtn, confirmBtn);
    dialog.append(title, content, btnGroup);
    overlay.append(dialog);
  
    // 添加动画样式
    const style = document.createElement('style');
    style.textContent = `
      @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
      }
      @keyframes slideIn {
        from { transform: translateY(-20px); opacity: 0; }
        to { transform: translateY(0); opacity: 1; }
      }
    `;
    document.head.append(style);
  
    return overlay;
  }
  
  // 使用示例
  document.querySelector('#logoutBtn').addEventListener('click', function(e) {
    e.preventDefault();
    const modal = createLogoutConfirm(() => {
      document.querySelector('#logoutForm').submit();
    });
    document.body.append(modal);
  });
  
  function showSection2(sectionId) {
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
      
      //if (sectionId === 'userManagement') {
          //loadUsers();
     // }
      
  }
  
  // 初始化显示 Deploy 模块
  //showSection2('deploy');
  let currentPage = 1; // 当前页码
  const perPage = 5; // 每页显示的条目数
  
  /**
   * 显示右上角 Toast 通知
   * @param {string} icon - 图标类型（success, error, warning, info, question）
   * @param {string} title - 提示标题
   * @param {number} [timer=3000] - 自动关闭时间（毫秒）
   */
  function showToast(icon, title, timer = 3000) {
      // 关闭所有现存弹窗
      Swal.close();
  
      // 使用 mixin 保持队列
      const Toast = Swal.mixin({
          toast: true,
          position: 'top-end',
          showConfirmButton: false,
          timer: timer,
          timerProgressBar: true,
          didOpen: (toast) => {
              toast.addEventListener('mouseenter', Swal.stopTimer);
              toast.addEventListener('mouseleave', Swal.resumeTimer);
          }
      });
  
      Toast.fire({
          icon: icon,
          title: title
      });
  }
  // 滚动锁定管理
  let scrollPosition = 0;
  
  function lockScroll2() {
      scrollPosition = window.pageYOffset;
      document.documentElement.style.cssText = `
          position: fixed;
          top: -${scrollPosition}px;
          left: 0;
          width: 100%;
          overflow: hidden;
      `;
  }
  
  // 修改后的滚动控制函数
  
  
  function lockScroll() {
    scrollPosition = window.pageYOffset;
    document.documentElement.style.setProperty('--scroll-y', `${scrollPosition}px`);
    document.documentElement.classList.add('noscroll');
  }
  
  function unlockScroll() {
    document.documentElement.classList.remove('noscroll');
    const scrollY = document.documentElement.style.getPropertyValue('--scroll-y');
    window.scrollTo(0, parseInt(scrollY || '0'));
    document.documentElement.style.removeProperty('--scroll-y');
  }
  
  
  function unlockScroll2() {
      document.documentElement.style.cssText = '';
      window.scrollTo(0, scrollPosition);
  }
  
  
  async function restartServices(env, modelName, modelVersion) {
      // 在restartServices函数开头添加
      let scrollPosition = window.pageYOffset || document.documentElement.scrollTop;
      document.documentElement.style.top = `-${scrollPosition}px`;
      document.documentElement.classList.add('noscroll');
      lockScroll();
      const restartButton = document.querySelector(`button[onclick="restartServices('${env}', '${modelName}', '${modelVersion}')"]`);
      
      const overlay = document.createElement('div');
      overlay.className = 'loading-overlay';
      // 优化后的弹窗结构
      // const overlay = document.createElement('div')
  
  
      overlay.innerHTML = `
          <div class="loading-overlay-inner">
              <div class="version-card">
                  <div class="version-header">
                      <i class="bi bi-cloud-check"></i>
                      <h3>Service Restarting</h3>
                  </div>
                  
                  <div class="version-details">
                      <div class="version-detail">
                          <div class="version-label">Environment</div>
                          <div class="version-value">${env.toUpperCase()}</div>
                      </div>
                      <div class="version-detail">
                          <div class="version-label">Model Name</div>
                          <div class="version-value" data-tooltip="${modelName}">${modelName}</div>
                      </div>
                      <div class="version-detail">
                          <div class="version-label">Version</div>
                          <div class="version-value">v${modelVersion}</div>
                      </div>
                      <div class="version-detail">
                          <div class="version-label">Status</div>
                          <div class="version-value text-warning">Initializing</div>
                      </div>
                      <!-- 新增错误信息区域 -->
                      <div class="version-detail error-detail" style="display: none;">
                          <div class="version-label">Error</div>
                          <div class="version-value text-danger error-message"></div>
                      </div>
                  </div>
  
                  <div class="loading-status">
                      <i class="bi bi-arrow-repeat spinning-icon"></i>
                      <span>Processing your request...</span>
                  </div>
              </div>
          </div>
      `;
  
      document.body.appendChild(overlay);
      let result;
  
      try {
          const statusElement = overlay.querySelector('.version-value.text-warning');
          statusElement.textContent = 'In Progress';
  
          const response = await fetch('/restart_services', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ 
                  env, 
                  model_name: modelName, 
                  model_version: modelVersion 
              })
          });
  
          result = await response.json();
          
          if (result.status === 'success') {
              statusElement.textContent = 'Completed';
              statusElement.className = 'version-value text-success';
          } else {
              statusElement.textContent = 'Failed';
              statusElement.className = 'version-value text-danger';
              // 显示错误详细信息
              const errorDetail = overlay.querySelector('.error-detail');
              const errorMessage = errorDetail.querySelector('.error-message');
              errorDetail.style.display = 'flex';
              errorMessage.textContent = result.message || 'No error message provided';
          }
  
      } catch (error) {
          const statusElement = overlay.querySelector('.version-value.text-warning');
          statusElement.textContent = 'Network Error';
          statusElement.className = 'version-value text-danger';
          // 显示网络错误详细信息
          const errorDetail = overlay.querySelector('.error-detail');
          const errorMessage = errorDetail.querySelector('.error-message');
          errorDetail.style.display = 'flex';
          errorMessage.textContent = error.message || 'Failed to connect to server';
          console.error('Restart failed:', error);
          result = { status: 'error' };
      } finally {
          const delay = result?.status === 'success' ? 1500 : 3000;
          setTimeout(() => {
              overlay.style.animation = 'fadeOut 0.3s ease forwards';
              setTimeout(() => {
                  overlay.remove();
                  unlockScroll();
                  
                  if (result?.status === 'success') {
                      loadModelVersions(env, modelName);
                      checkServiceStatus(env, modelName, modelVersion);
                  }
              }, 300);
          }, delay);
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
  
  // 其他 JavaScript 代码保持不变...
  
  //let currentLogFile = null;  // 当前选中的日志文件
  
  // 动态切换文件或文件夹上传
  
   // 上传类型切换
  
  // 修改后的 loadLogFiles 函数
  // 增强版的初始化逻辑
  
  // 优化后的 JavaScript 代码
  let isLoading = false;
  let isInitialLoad = true;
  let currentLogFile = null;
  let refreshInterval = null;
  
  async function loadLogFiles() {
      const container = document.getElementById('logFiles');
      if (!container || isLoading) return;
  
      try {
          isLoading = true;
          toggleLoadingState(true);
  
          const response = await fetch(`/log_files?t=${Date.now()}`, {
              headers: { 'Cache-Control': 'no-cache' }
          });
  
          if (!response.ok) throw new Error(`HTTP ${response.status}`);
  
          const result = await response.json();
          if (result.status === 'success') {
              // 先添加临时加载效果
              //container.style.opacity = '0.5';
              container.innerHTML = renderFileList(result.log_files);
              if (isInitialLoad) {
                  container.style.opacity = '1';
                  isInitialLoad = false;
                  
              }
  
          } else {
              throw new Error(result.message);
          }
      } catch (error) {
          console.error('加载失败:', error);
          container.innerHTML = renderErrorState(error.message);
      } finally {
          isLoading = false;
          toggleLoadingState(false);
      }
  }
  
  function toggleLoadingState(loading) {
    const btn = document.getElementById('refreshLogsButton');
    if (!btn) return;
  
    // 更明显的按钮状态变化
    btn.disabled = loading;
    btn.style.opacity = loading ? 0.7 : 1;
    
    // 图标动画控制
    const icon = btn.querySelector('i');
    icon.className = loading 
      ? 'bi bi-arrow-clockwise spin'  // 同时保留原类名
      : 'bi bi-arrow-clockwise';
      
    // 文字状态反馈
    const textSpan = btn.querySelector('span');
    textSpan.textContent = loading ? '加载中...' : '刷新列表';
  }
  
  
  
  
  function renderErrorState(message) {
      return `
          <div class="alert alert-danger m-3">
              <i class="bi bi-exclamation-triangle me-2"></i>
              ${message}
          </div>
      `;
  }
  
  function renderFileList(files) {
      if (!files || !files.length) return renderEmptyState();
  
      return files.map(file => {
          const safeFile = {
              name: escapeHtml(file.name || '未知文件'),
              size: formatFileSize(file.size || 0),
              modified_time: formatDateTime(file.modified_time) || '未知时间'
          };
  
          const fileData = JSON.stringify(safeFile)
                            .replace(/</g, '\\u003c')
                            .replace(/'/g, '&apos;');
  
          return `
              <div class="log-file-item p-3 border-bottom hover-effect">
                  <div class="d-flex justify-content-between align-items-center">
                      <div class="flex-grow-1 me-3">
                          <div class="d-flex align-items-center mb-2">
                              <i class="bi bi-file-text me-2 text-primary fs-5"></i>
                              <strong class="text-truncate">${safeFile.name}</strong>
                          </div>
                          <div class="d-flex text-muted small">
                              <span class="me-3">
                                  <i class="bi bi-clock-history me-1"></i>
                                  ${safeFile.modified_time}
                              </span>
                              <span>
                                  <i class="bi bi-hdd me-1"></i>
                                  ${safeFile.size}
                              </span>
                          </div>
                      </div>
                      <button class="btn btn-sm btn-outline-primary view-log-btn"
                              data-file='${fileData}'
                              title="查看完整日志">
                          <i class="bi bi-eye me-1"></i>
                          <span class="d-none d-md-inline">查看</span>
                      </button>
                  </div>
              </div>
          `;
      }).join('');
  }
  
  function escapeHtml(str) {
      return str.toString()
          .replace(/&/g, "&amp;")
          .replace(/</g, "&lt;")
          .replace(/>/g, "&gt;")
          .replace(/"/g, "&quot;")
          .replace(/'/g, "&#039;");
  }
  
  function formatFileSize(bytes) {
      const units = ['B', 'KB', 'MB', 'GB'];
      let size = Number(bytes) || 0;
      let unitIndex = 0;
  
      while (size >= 1024 && unitIndex < units.length - 1) {
          size /= 1024;
          unitIndex++;
      }
      return `${size.toFixed(unitIndex > 0 ? 1 : 0)} ${units[unitIndex]}`;
  }
  
  function formatDateTime(timestamp) {
      try {
          return new Date(timestamp).toLocaleString('zh-CN', {
              year: 'numeric',
              month: '2-digit',
              day: '2-digit',
              hour: '2-digit',
              minute: '2-digit',
              second: '2-digit'
          });
      } catch (e) {
          return timestamp;
      }
  }
  
  function renderEmptyState() {
      return `
          <div class="text-center p-4 text-muted">
              <i class="bi bi-folder-x display-5 mb-3"></i>
              <p class="mb-0">当前没有可用的日志文件</p>
              <small>请检查日志目录或联系系统管理员</small>
          </div>
      `;
  }
  
  document.addEventListener('DOMContentLoaded', () => {
      const init = () => {
          const btn = document.getElementById('refreshLogsButton');
          if (btn) {
              btn.addEventListener('click', loadLogFiles);
              loadLogFiles();
              return true;
          }
          return false;
      };
  
      if (!init()) {
          const checkInterval = setInterval(() => {
              if (init()) clearInterval(checkInterval);
          }, 100);
      }
  });
  
  // 增加旋转动画
  const style = document.createElement('style');
  style.textContent = `
  @keyframes spin { 
      100% { transform: rotate(360deg); } 
  }
  .bi-arrow-clockwise.spin {
      animation: spin 1s linear infinite;
  }`;
  document.head.appendChild(style);
  
  
  document.addEventListener('click', (e) => {
      const btn = e.target.closest('.view-log-btn');
      if (btn) {
          try {
              const fileData = JSON.parse(btn.dataset.file);
              selectLogFile(fileData);
          } catch (error) {
              console.error('文件数据解析失败:', error);
              showToast('文件信息异常，请刷新重试', 'danger');
          }
      }
  });
  
  async function selectLogFile(fileInfo) {
      const modal = new bootstrap.Modal('#logModal');
      currentLogFile = encodeURIComponent(fileInfo.name);
  
      try {
          document.querySelector('#logModal .modal-title').textContent = fileInfo.name;
          await loadLogContent();
      } catch (error) {
          console.error('初始化日志失败:', error);
          document.querySelector('#logModal pre').innerHTML = `
              <div class="alert alert-danger m-3">
                  ${error.message}
              </div>
          `;
      }
  
      modal.show();
  }
  
  async function loadLogContent() {
      if (!currentLogFile) return;
  
      const linesInput = document.getElementById('logLines');
      const loading = document.querySelector('.log-loading');
      const contentElement = document.querySelector('#logModal pre');
  
      // 校验并限制行数范围
      let lines = parseInt(linesInput.value) || 500;
      lines = Math.min(Math.max(lines, 100), 5000);
      linesInput.value = lines;
  
      try {
          // 显示加载状态
          contentElement.innerHTML = '<div class="text-center py-4"><div class="spinner-border"></div></div>';
          loading.classList.remove('hidden');
  
          // 发起请求
          const response = await fetch(`/log_content?file=${currentLogFile}&lines=${lines}`);
          if (!response.ok) throw new Error(`HTTP错误 ${response.status}`);
  
          // 解析响应
          const result = await response.json();
          if (result.status === 'success') {
              // 检查内容长度是否为空
              if (result.content && result.content.length > 0) {
                  contentElement.textContent = result.content;
                  // console.log("result.conten",result.content)
              } else {
                  contentElement.textContent = "暂无日志信息";
                     
              }
          } else {
              throw new Error(result.message || "未知错误");
          }
      } catch (error) {
          // 显示错误信息
          contentElement.innerHTML = `
              <div class="alert alert-danger m-3">
                  <i class="bi bi-exclamation-triangle me-2"></i>
                  加载失败: ${error.message}
              </div>`;
      } finally {
          // 隐藏加载状态
          loading.classList.add('hidden');
      }
  }
  
  
  let searchTimeout;
  document.getElementById('logLines').addEventListener('input', () => {
      clearTimeout(searchTimeout);
      searchTimeout = setTimeout(loadLogContent, 500);
  });
  
  document.getElementById('logModal').addEventListener('hidden.bs.modal', () => {
      clearInterval(refreshInterval);
      currentLogFile = null;
  });
  
  
  
  // 初始化加载
  window.onload = loadLogFiles;
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
      // showSection('modelVersions');
  
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
                  if (result.model_names.length < 1) {
                      modelNamesList.innerHTML = `
                          <div class="text-center py-5">
                              <div class="text-muted mb-3">
                                  暂无模型，请
                                  <a href="javascript:void(0)"
                                     class="text-primary text-decoration-underline cursor-pointer"
                                     onclick="showDocumentation()"
                                     id="addModelLink"
                                     role="button"
                                     tabindex="0">
                                      添加
                                  </a>
                              </div>
                          </div>
                      `;
                      // 清空分页控件
                      document.getElementById('pagination').innerHTML = '';
                      return;
                  }
  
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
                  // 清空分页控件
                  document.getElementById('pagination').innerHTML = '';
              }
          })
          .catch(error => {
              console.error("Error loading model names:", error);
              modelNamesList.innerHTML = '<div class="text-danger">An error occurred. Please try again later.</div>';
              // 清空分页控件
              document.getElementById('pagination').innerHTML = '';
          });
  }
  
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
          loadModelNames(env, 1); // 重置为第一页
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
  
  async function saveConfig() {
      try {
          const newConfig = editor.get();
          const response = await fetch('/update_config', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                  env: currentEnv,
                  model_name: currentModelName,
                  config: newConfig
              }),
          });
  
          // 增强HTTP错误处理
          if (!response.ok) {
              let serverError = `HTTP Error (${response.status})`;
              try {
                  const errorBody = await response.json();
                  if (errorBody.message) serverError = errorBody.message;
              } catch (e) {
                  // 如果响应不是JSON格式则保持默认错误信息
              }
              throw new Error(serverError);
          }
  
          const result = await response.json();
          if (result.status === 'success') {
              console.log('[Toast调试] 显示成功提示');
              showToast('success', 'Config updated successfully!');
              cancelEdit();
              hideConfigManagement();
              loadModelNames(currentEnv, currentPage);
          } else {
              // 处理业务逻辑错误
              throw new Error(result.message || 'Configuration validation failed');
          }
      } catch (error) {
          console.error("Config save error:", error);
          console.groupCollapsed('[错误追踪] 配置保存失败');
          console.log('错误对象:', error);
          console.log('错误类型:', error?.constructor?.name);
          console.log('错误栈:', error?.stack);
          console.groupEnd();
          // 显示完整的错误链信息
          const errorMessage = error instanceof Error ?
              `${error.message}${error.cause ? ` (${error.cause})` : ''}` :
              'Unknown configuration error';
  
          console.log('[Toast调试] 显示错误提示');
          showToast("error", `Save failed: ${errorMessage}`, 5000);
      }
  }
  
  // 保存配置文件
  async function saveConfig22() {
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
      
      // ... 保留之前的元素获取和验证代码 ...
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
  
      fetch(`/operation_records?page=${page}&per_page=${logsPerPage}`)
          .then(response => response.json())
          .then(result => {
              if (result.status === 'success') {
                  // ... 保留表格内容生成代码 ...
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
  
                  // 分页生成优化
                  const totalPages = Math.ceil(result.total / logsPerPage);
                  const paginationContent = generatePagination(totalPages);
  
                  // 更新分页内容
                  pagination.querySelector('ul').innerHTML = paginationContent;
              }
          }).catch(error => {
              console.error('加载操作日志失败:', error);
              tableBody.innerHTML = `
                  <tr>
                      <td colspan="4" class="text-center text-danger">
                          <i class="bi bi-exclamation-triangle"></i> 加载失败，请稍后重试。
                      </td>
                  </tr>
              `;
          });
          // ... 保留错误处理代码 ...
  }
  
  // 新的分页生成函数
  function generatePagination(totalPages) {
      const maxVisiblePages = 5; // 最多显示5个页码按钮
      let startPage, endPage;
  
      if (totalPages <= maxVisiblePages) {
          // 全部显示
          startPage = 1;
          endPage = totalPages;
      } else {
          // 计算动态范围
          const maxLeft = Math.floor(maxVisiblePages / 2);
          startPage = currentLogPage - maxLeft;
          endPage = currentLogPage + maxLeft;
  
          if (startPage < 1) {
              endPage += 1 - startPage;
              startPage = 1;
          }
          if (endPage > totalPages) {
              startPage -= endPage - totalPages;
              endPage = totalPages;
          }
      }
  
      // 生成页码按钮
      const pageButtons = [];
      
      // 上一页按钮
      const prevDisabled = currentLogPage === 1;
      pageButtons.push(`
          <li class="page-item ${prevDisabled ? 'disabled' : ''}">
              <a class="page-link" href="#" onclick="loadOperationLogs(${currentLogPage - 1})">
                  <i class="bi bi-arrow-left"></i>
              </a>
          </li>
      `);
  
      // 起始省略号
      if (startPage > 1) {
          pageButtons.push(`
              <li class="page-item">
                  <a class="page-link" href="#" onclick="loadOperationLogs(1)">1</a>
              </li>
              ${startPage > 2 ? '<li class="page-item disabled"><span class="page-link">...</span></li>' : ''}
          `);
      }
  
      // 页码按钮
      for (let i = startPage; i <= endPage; i++) {
          const isActive = i === currentLogPage;
          pageButtons.push(`
              <li class="page-item ${isActive ? 'active' : ''}">
                  <a class="page-link" href="#" onclick="loadOperationLogs(${i})">${i}</a>
              </li>
          `);
      }
  
      // 结尾省略号
      if (endPage < totalPages) {
          pageButtons.push(`
              ${endPage < totalPages - 1 ? '<li class="page-item disabled"><span class="page-link">...</span></li>' : ''}
              <li class="page-item">
                  <a class="page-link" href="#" onclick="loadOperationLogs(${totalPages})">${totalPages}</a>
              </li>
          `);
      }
  
      // 下一页按钮
      const nextDisabled = currentLogPage === totalPages;
      pageButtons.push(`
          <li class="page-item ${nextDisabled ? 'disabled' : ''}">
              <a class="page-link" href="#" onclick="loadOperationLogs(${currentLogPage + 1})">
                  <i class="bi bi-arrow-right"></i>
              </a>
          </li>
      `);
  
      return pageButtons.join('');
  }
  
  function loadOperationLogs22(page = 1) {
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
  
  //用户管理
  // 显示用户管理页面
  
  
  // 获取用户列表并渲染表格
  // 加载用户数据
  // static/js/scripts.js
  
  
  // 格式化日期时间
  function formatDate(dateString) {
      if (!dateString) return '未知时间';
      const date = new Date(dateString);
      const year = date.getFullYear();
      const month = String(date.getMonth() + 1).padStart(2, '0');
      const day = String(date.getDate()).padStart(2, '0');
      const hours = String(date.getHours()).padStart(2, '0');
      const minutes = String(date.getMinutes()).padStart(2, '0');
      return `${year}-${month}-${day} ${hours}:${minutes}`;
  }
  
  
  
  
  // 在scripts.js顶部添加（仅执行一次）
  (function injectAnimations() {
      if (!document.getElementById('custom-animations')) {
          const animationStyle = document.createElement('style'); // 重命名变量
          animationStyle.id = 'custom-animations';
          animationStyle.textContent = `
              @keyframes fadeIn {
                  from { opacity: 0; }
                  to { opacity: 1; }
              }
              @keyframes fadeOut {
                  from { opacity: 1; }
                  to { opacity: 0; }
              }
          `;
          document.head.appendChild(animationStyle);
      }
  })();
  
  // 在全局作用域定义函数
  // ====================== 文档中心功能 ======================
  window.showDocumentation = async function() {
      // 防页面晃动预处理
      const scrollbarWidth = window.innerWidth - document.documentElement.clientWidth;
      document.body.style.paddingRight = `${scrollbarWidth}px`;
      document.body.classList.add('modal-open');
      
      // 防抖动预处理
      document.documentElement.style.overflow = 'hidden';
  
  
      // 创建遮罩层
      const overlay = document.createElement('div');
      Object.assign(overlay.style, {
          position: 'fixed',
          top: '0',
          left: '0',
          width: '100vw',
          height: '100vh',
          background: 'rgba(17, 24, 39, 0.8)',
          backdropFilter: 'blur(8px)',
          zIndex: '9999',
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          opacity: '0',
          transition: 'opacity 0.3s ease'
      });
  
      // 内容容器
      const container = document.createElement('div');
      Object.assign(container.style, {
          position: 'relative',
          width: 'min(90%, 1200px)',
          height: 'min(80vh, 800px)',
          background: '#ffffff',
          borderRadius: '16px',
          boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1)',
          overflow: 'hidden',
          transform: 'scale(0.95)',
          transition: 'transform 0.3s ease'
      });
  
      // 标题栏
      const header = document.createElement('div');
      Object.assign(header.style, {
          padding: '24px',
          background: '#f8fafc',
          borderBottom: '1px solid #e2e8f0',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
      });
      header.innerHTML = `
          <div style="display: flex; align-items: center; gap: 12px">
              <svg style="width: 24px; height: 24px; color: #3b82f6" viewBox="0 0 24 24">
                  <path fill="currentColor" d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6z"/>
                  <path fill="currentColor" d="M14 2v6h6m-4 5H8v2h8v-2zM8 15h8v2H8v-2z"/>
              </svg>
              <h2 style="margin:0; font-size: 1.5rem; color: #1e293b">系统文档</h2>
          </div>
          <button class="close-btn" style="
              background: none;
              border: none;
              padding: 8px;
              border-radius: 50%;
              cursor: pointer;
              transition: background 0.2s;
              color: #64748b
          ">
              <svg style="width: 24px; height: 24px" viewBox="0 0 24 24">
                  <path fill="currentColor" d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
              </svg>
          </button>
      `;
  
      // 内容区域
      const content = document.createElement('div');
      Object.assign(content.style, {
          height: 'calc(100% - 80px)',
          padding: '32px',
          overflowY: 'auto',
          scrollBehavior: 'smooth'
      });
  
      // 加载状态
      content.innerHTML = `
          <div style="
              display: flex;
              flex-direction: column;
              align-items: center;
              justify-content: center;
              height: 100%;
              gap: 16px;
              color: #64748b
          ">
              <div class="spinner" style="
                  width: 48px;
                  height: 48px;
                  border: 4px solid #e2e8f0;
                  border-top-color: #3b82f6;
                  border-radius: 50%;
                  animation: spin 1s linear infinite
              "></div>
              <p style="margin:0; font-size: 1rem">文档加载中...</p>
          </div>
      `;
  
      // 组装元素
      container.appendChild(header);
      container.appendChild(content);
      overlay.appendChild(container);
      document.body.appendChild(overlay);
  
      // 动画触发
      setTimeout(() => {
          overlay.style.opacity = '1';
          container.style.transform = 'scale(1)';
      }, 10);
  
      // 关闭处理
      const closeHandler = () => {
          overlay.style.opacity = '0';
          container.style.transform = 'scale(0.95)';
          setTimeout(() => {
              overlay.remove();
              document.body.style.paddingRight = '';
              document.body.classList.remove('modal-open');
              document.documentElement.style.overflow = '';
          }, 300);
      };
  
      // 事件绑定
      overlay.querySelector('.close-btn').addEventListener('click', closeHandler);
      overlay.addEventListener('click', e => e.target === overlay && closeHandler());
      
      // 精准点击区域检测
      overlay.addEventListener('click', e => {
          const containerRect = container.getBoundingClientRect();
          const clickX = e.clientX;
          const clickY = e.clientY;
          
          const isOutside = clickX < containerRect.left - 20 || 
                          clickX > containerRect.right + 20 ||
                          clickY < containerRect.top - 20 ||
                          clickY > containerRect.bottom + 20;
          
          if (isOutside) closeHandler();
      });
  
      // ESC键支持
      const escHandler = (e) => e.key === 'Escape' && closeHandler();
      document.addEventListener('keydown', escHandler);
  
      // 清理事件监听
      overlay.addEventListener('animationend', () => {
          document.removeEventListener('keydown', escHandler);
      }, {once: true});
      
  
      // 加载内容
      try {
          const response = await fetch('/get_readme');
          const markdown = await response.text();
          
          // 渲染Markdown
          const html = marked.parse(markdown);
          const tempDiv = document.createElement('div');
          tempDiv.innerHTML = html;
  
          // 样式处理
          const styledContent = `
              <style>
                  .doc-content {
                      line-height: 1.75;
                      font-size: 16px;
                      color: #334155;
                  }
                  .doc-content h2 {
                      color: #1e293b;
                      font-size: 1.5rem;
                      margin: 2em 0 1em;
                      padding-bottom: 0.5em;
                      border-bottom: 2px solid #e2e8f0;
                  }
                  .doc-content pre {
                      position: relative;
                      background: #f8fafc;
                      border-radius: 8px;
                      padding: 1.5rem;
                      margin: 1.5rem 0;
                      overflow-x: auto;
                  }
                  .doc-content code {
                      font-family: 'SFMono-Regular', Consolas, monospace;
                      font-size: 14px;
                      color: #1e293b;
                  }
                  .copy-btn {
                      position: absolute;
                      top: 12px;
                      right: 12px;
                      width: 28px;
                      height: 28px;
                      padding: 4px;
                      border: 1px solid #e2e8f0;
                      border-radius: 6px;
                      background: white;
                      cursor: pointer;
                      transition: all 0.2s;
                      display: flex;
                      align-items: center;
                      justify-content: center;
                  }
                  .copy-btn:hover {
                      background: #3b82f6;
                      border-color: #3b82f6;
                  }
                  .copy-btn:hover svg {
                      stroke: white;
                  }
              </style>
              <div class="doc-content">${tempDiv.innerHTML}</div>
          `;
  
          content.innerHTML = styledContent;
  
          // 添加代码复制功能
          content.querySelectorAll('pre').forEach(pre => {
              const btn = document.createElement('button');
              btn.className = 'copy-btn';
              btn.innerHTML = `
                  <svg width="16" height="16" viewBox="0 0 24 24">
                      <path fill="currentColor" d="M16 1H4c-1.1 0-2 .9-2 2v14h2V3h12V1zm3 4H8c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h11c1.1 0 2-.9 2-2V7c0-1.1-.9-2-2-2zm0 16H8V7h11v14z"/>
                  </svg>
              `;
              
              btn.onclick = async () => {
                  try {
                      const code = pre.querySelector('code').textContent;
                      if (navigator.clipboard) {
                          await navigator.clipboard.writeText(code);
                      } else {
                          // 兼容旧版浏览器
                          const textarea = document.createElement('textarea');
                          textarea.value = code;
                          document.body.appendChild(textarea);
                          textarea.select();
                          document.execCommand('copy');
                          document.body.removeChild(textarea);
                      }
                      btn.innerHTML = `
                          <svg width="16" height="16" viewBox="0 0 24 24">
                              <path fill="#10b981" d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/>
                          </svg>
                      `;
                      setTimeout(() => {
                          btn.innerHTML = `
                              <svg width="16" height="16" viewBox="0 0 24 24">
                                  <path fill="currentColor" d="M16 1H4c-1.1 0-2 .9-2 2v14h2V3h12V1zm3 4H8c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h11c1.1 0 2-.9 2-2V7c0-1.1-.9-2-2-2zm0 16H8V7h11v14z"/>
                              </svg>
                          `;
                      }, 2000);
                  } catch (error) {
                      console.error('复制失败:', error);
                      btn.innerHTML = `
                          <svg width="16" height="16" viewBox="0 0 24 24">
                              <path fill="#ef4444" d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z"/>
                          </svg>
                      `;
                  }
              };
              pre.prepend(btn);
          });
  
      } catch (error) {
          content.innerHTML = `
              <div style="
                  background: #fff4f4;
                  border: 1px solid #fed7d7;
                  color: #dc2626;
                  padding: 24px;
                  border-radius: 8px;
                  margin: 24px;
                  display: flex;
                  gap: 12px;
                  align-items: center
              ">
                  <svg style="width: 24px; height: 24px" viewBox="0 0 24 24">
                      <path fill="currentColor" d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z"/>
                  </svg>
                  <div>
                      <h3 style="margin:0 0 8px; color: #b91c1c">文档加载失败</h3>
                      <p style="margin:0">${error.message}</p>
                  </div>
              </div>
          `;
      }
  
      // 动画样式
      if (!document.getElementById('doc-anim-style')) {
          const style = document.createElement('style');
          style.id = 'doc-anim-style';
          style.textContent = `
              @keyframes spin {
                  to { transform: rotate(360deg); }
              }
          `;
          document.head.appendChild(style);
      }
  };
  
  // ====================== 初始化事件绑定 ======================
  document.addEventListener('DOMContentLoaded', () => {
      const docBtn = document.getElementById('docCenterBtn');
      if (docBtn) {
          docBtn.addEventListener('click', e => {
              e.preventDefault();
              window.showDocumentation();
          });
      }
  });
  
  window.closeDocumentation = function() {
      const overlay = document.querySelector('div[style*="background: rgba(0,0,0,0.7)"]');
      if (overlay) {
          overlay.style.animation = 'fadeOut 0.3s ease forwards';
          setTimeout(() => {
              overlay.remove();
              document.body.style.overflow = '';
          }, 300);
      }
  }
  
  
  // 动态加载节点数据
  // 在之前的loadNodes函数中添加
  async function loadNodes() {
    try {
      const response = await fetch('/api/nodes');
      const { data: nodes } = await response.json();
      const selector = document.getElementById('nodeSelector');
  
      // 清空选项
      selector.innerHTML = '';
  
      // 填充节点选项
      nodes.forEach(node => {
        const option = new Option(`${node.name} (${parseHost(node.url)})`, node.url);
        selector.appendChild(option);
      });
  
      // 添加选择监听
      selector.addEventListener('change', function() {
        const selectedUrl = this.value;
        if (!selectedUrl) return;
        
        // 创建确认弹窗
        const modal = createConfirmModal(
          `切换到 ${this.options[this.selectedIndex].text}`,
          `确定要切换至该计算节点？`,
          () => {
            const currentParams = window.location.search;
            window.location.href = selectedUrl + currentParams;
          },
          () => this.value = this.dataset.current // 恢复选中状态
        );
        
        document.body.appendChild(modal);
      });
  
      // 初始化选中状态
      if (nodes.length > 0) {
        selector.value = nodes[0].url;
        selector.dataset.current = nodes[0].url;
      }
  
    } catch (error) {
      console.error('节点加载失败:', error);
      selector.innerHTML = '<option value="">节点加载失败</option>';
    }
  }
  
  /* 工具函数 */
  const parseHost = url => {
    try {
      const { hostname, port } = new URL(url);
      return `${hostname}:${port}`;
    } catch {
      return url;
    }
  };
  
  const createConfirmModal = (title, message, onConfirm, onCancel) => {
    // 创建容器
    const container = document.createElement('div');
    container.style = `
      position: fixed;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      background: rgba(0,0,0,0.5);
      display: flex;
      justify-content: center;
      align-items: center;
      z-index: 1000;
    `;
  
    // 对话框内容
    const dialog = document.createElement('div');
    dialog.style = `
      background: white;
      padding: 24px;
      border-radius: 8px;
      box-shadow: 0 4px 16px rgba(0,0,0,0.15);
      width: 320px;
    `;
  
    // 标题
    const titleEl = document.createElement('h3');
    titleEl.textContent = title;
    titleEl.style = `
      margin: 0 0 12px;
      font-size: 18px;
      color: #1a1a1a;
    `;
  
    // 内容
    const messageEl = document.createElement('p');
    messageEl.textContent = message;
    messageEl.style = `
      margin: 0 0 20px;
      color: #666;
      line-height: 1.5;
    `;
  
    // 按钮容器
    const buttonGroup = document.createElement('div');
    buttonGroup.style = `
      display: flex;
      gap: 12px;
      justify-content: flex-end;
    `;
  
    // 确认按钮
    const confirmBtn = document.createElement('button');
    confirmBtn.textContent = '确认切换';
    confirmBtn.style = `
      padding: 8px 16px;
      background: #4f46e5;
      color: white;
      border: none;
      border-radius: 4px;
      cursor: pointer;
      transition: background 0.2s;
    `;
    confirmBtn.onmouseover = () => confirmBtn.style.background = '#4338ca';
    confirmBtn.onclick = () => {
      container.remove();
      onConfirm();
    };
  
    // 取消按钮
    const cancelBtn = document.createElement('button');
    cancelBtn.textContent = '取消';
    cancelBtn.style = `
      padding: 8px 16px;
      background: #f1f5f9;
      color: #64748b;
      border: none;
      border-radius: 4px;
      cursor: pointer;
      transition: background 0.2s;
    `;
    cancelBtn.onmouseover = () => cancelBtn.style.background = '#e2e8f0';
    cancelBtn.onclick = () => {
      container.remove();
      onCancel();
    };
  
    // 组装元素
    buttonGroup.append(cancelBtn, confirmBtn);
    dialog.append(titleEl, messageEl, buttonGroup);
    container.append(dialog);
  
    return container;
  };
  
  // 页面加载时执行
  document.addEventListener('DOMContentLoaded', () => {
    loadNodes();
    
    // 监听选择变化
    document.getElementById('nodeSelector').addEventListener('change', (e) => {
      console.log('当前选择节点:', e.target.value);
      // 这里可以添加节点切换逻辑
    });
  });
  
  
  
  
  