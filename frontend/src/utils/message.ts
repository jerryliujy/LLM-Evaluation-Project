// 简单的消息提示工具函数
export const showMessage = (message: string, type: 'success' | 'error' | 'warning' = 'success') => {
  // 创建临时提示元素
  const msgEl = document.createElement('div')
  msgEl.textContent = message
  msgEl.style.cssText = `
    position: fixed;
    top: 20px;
    left: 50%;
    transform: translateX(-50%);
    padding: 12px 24px;
    border-radius: 6px;
    color: white;
    font-size: 14px;
    z-index: 9999;
    background: ${type === 'success' ? '#67c23a' : type === 'error' ? '#f56c6c' : '#e6a23c'};
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
    transition: opacity 0.3s ease;
  `
  
  document.body.appendChild(msgEl)
  
  // 3秒后淡出并移除
  setTimeout(() => {
    msgEl.style.opacity = '0'
    setTimeout(() => {
      if (msgEl.parentNode) {
        msgEl.parentNode.removeChild(msgEl)
      }
    }, 300)
  }, 3000)
}

// 模拟 ElMessage 的 API
export const ElMessage = {
  success: (message: string) => showMessage(message, 'success'),
  error: (message: string) => showMessage(message, 'error'),
  warning: (message: string) => showMessage(message, 'warning')
}
