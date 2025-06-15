<template>
  <div class="invite-code-copy">
    <div class="invite-section">
      <h3>我的邀请码</h3>
      
      <div v-if="loading" class="loading">
        加载中...
      </div>
      
      <div v-else-if="inviteCode" class="invite-code-container">
        <div class="code-display">
          <span class="code-text">{{ inviteCode }}</span>
          <button 
            @click="copyInviteCode" 
            class="copy-btn"
            :disabled="copying"
          >
            {{ copying ? '复制中...' : '📋 复制' }}
          </button>
        </div>
        <p class="code-description">
          点击复制按钮将邀请码复制到剪贴板，分享给需要的用户
        </p>
      </div>
      
      <div v-else class="no-invite-code">
        <p>您还没有邀请码</p>
        <p class="help-text">邀请码会在用户注册时自动生成（仅限管理员）</p>
      </div>
    </div>

    <!-- 成功提示 -->
    <div v-if="successMessage" class="success-toast">
      {{ successMessage }}
    </div>

    <!-- 错误提示 -->
    <div v-if="errorMessage" class="error-toast">
      {{ errorMessage }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { authService } from '@/services/authService'

// 响应式数据
const inviteCode = ref('')
const loading = ref(false)
const copying = ref(false)
const successMessage = ref('')
const errorMessage = ref('')

// 生命周期
onMounted(() => {
  loadInviteCode()
})

// 方法
const loadInviteCode = async () => {
  loading.value = true
  try {
    const response = await authService.getMyInviteCode()
    inviteCode.value = response.invite_code
  } catch (error: any) {
    // 如果没有邀请码，不显示错误
    if (!error.message.includes('404') && !error.message.includes('No invite code')) {
      showError(error.message)
    }
  } finally {
    loading.value = false
  }
}

const copyInviteCode = async () => {
  if (!inviteCode.value) return
  
  copying.value = true
  try {
    await navigator.clipboard.writeText(inviteCode.value)
    showSuccess('邀请码已复制到剪贴板！')
  } catch (error) {
    // 降级处理：使用旧的API
    try {
      const textArea = document.createElement('textarea')
      textArea.value = inviteCode.value
      document.body.appendChild(textArea)
      textArea.select()
      document.execCommand('copy')
      document.body.removeChild(textArea)
      showSuccess('邀请码已复制到剪贴板！')
    } catch (fallbackError) {
      showError('复制失败，请手动复制邀请码')
    }
  } finally {
    copying.value = false
  }
}

const showSuccess = (message: string) => {
  successMessage.value = message
  setTimeout(() => {
    successMessage.value = ''
  }, 3000)
}

const showError = (message: string) => {
  errorMessage.value = message
  setTimeout(() => {
    errorMessage.value = ''
  }, 5000)
}
</script>

<style scoped>
.invite-code-copy {
  max-width: 600px;
  margin: 0 auto;
  padding: 20px;
}

.invite-section {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 24px;
  border: 1px solid #e9ecef;
}

.invite-section h3 {
  margin: 0 0 20px 0;
  color: #2c3e50;
  font-size: 20px;
  text-align: center;
}

.loading {
  text-align: center;
  padding: 20px;
  color: #6c757d;
  font-size: 16px;
}

.invite-code-container {
  text-align: center;
}

.code-display {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  margin-bottom: 16px;
  padding: 16px;
  background: white;
  border-radius: 6px;
  border: 2px solid #007bff;
}

.code-text {
  font-family: 'Courier New', monospace;
  font-size: 16px;
  font-weight: bold;
  color: #007bff;
  background: #e7f3ff;
  padding: 8px 12px;
  border-radius: 4px;
  letter-spacing: 1px;
}

.copy-btn {
  background: #007bff;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
  white-space: nowrap;
}

.copy-btn:hover:not(:disabled) {
  background: #0056b3;
  transform: translateY(-1px);
}

.copy-btn:disabled {
  background: #6c757d;
  cursor: not-allowed;
  transform: none;
}

.code-description {
  color: #6c757d;
  font-size: 14px;
  margin: 0;
  line-height: 1.4;
}

.no-invite-code {
  text-align: center;
  padding: 20px;
}

.no-invite-code p {
  margin: 8px 0;
  color: #6c757d;
}

.help-text {
  font-size: 14px;
  font-style: italic;
}

.success-toast {
  position: fixed;
  top: 20px;
  right: 20px;
  background: #28a745;
  color: white;
  padding: 12px 20px;
  border-radius: 4px;
  z-index: 1000;
  animation: slideIn 0.3s ease;
}

.error-toast {
  position: fixed;
  top: 20px;
  right: 20px;
  background: #dc3545;
  color: white;
  padding: 12px 20px;
  border-radius: 4px;
  z-index: 1000;
  animation: slideIn 0.3s ease;
}

@keyframes slideIn {
  from {
    transform: translateX(100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

/* 响应式设计 */
@media (max-width: 768px) {
  .invite-code-copy {
    padding: 16px;
  }
  
  .code-display {
    flex-direction: column;
    gap: 8px;
  }
  
  .code-text {
    font-size: 14px;
    word-break: break-all;
  }
}
</style>
