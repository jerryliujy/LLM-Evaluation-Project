<template>
  <div class="invite-code-manager">
    <div class="manager-header">
      <h3>邀请码管理</h3>
      <button 
        @click="showCreateDialog = true" 
        class="create-btn"
        :disabled="loading"
      >
        生成邀请码
      </button>
    </div>

    <!-- 邀请码列表 -->
    <div class="invite-codes-list">
      <div v-if="loading" class="loading">
        加载中...
      </div>
      
      <div v-else-if="inviteCodes.length === 0" class="empty-state">
        还没有生成任何邀请码
      </div>
      
      <div v-else class="codes-grid">
        <div 
          v-for="code in inviteCodes" 
          :key="code.id" 
          class="code-card"
          :class="{ 'expired': isExpired(code), 'used': code.is_used }"
        >
          <div class="code-header">
            <span class="code-text">{{ code.code }}</span>
            <div class="code-actions">
              <button 
                @click="copyToClipboard(code.code)" 
                class="copy-btn"
                title="复制邀请码"
              >
                📋
              </button>
              <button 
                v-if="!code.is_used && !isExpired(code)"
                @click="revokeCode(code.id)" 
                class="revoke-btn"
                title="撤销邀请码"
                :disabled="revoking === code.id"
              >
                🗑️
              </button>
            </div>
          </div>
          
          <div class="code-info">
            <div class="info-row">
              <span class="label">状态:</span>
              <span class="status" :class="getStatusClass(code)">
                {{ getStatusText(code) }}
              </span>
            </div>
            <div class="info-row">
              <span class="label">创建时间:</span>
              <span>{{ formatDate(code.created_at) }}</span>
            </div>
            <div class="info-row">
              <span class="label">过期时间:</span>
              <span>{{ formatDate(code.expires_at) }}</span>
            </div>
            <div v-if="code.is_used" class="info-row">
              <span class="label">使用时间:</span>
              <span>{{ formatDate(code.used_at!) }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 创建邀请码对话框 -->
    <div v-if="showCreateDialog" class="modal-overlay" @click="showCreateDialog = false">
      <div class="modal-content" @click.stop>
        <h4>生成邀请码</h4>
        <form @submit.prevent="createInviteCode">
          <div class="form-group">
            <label for="expires_in_hours">有效期（小时）:</label>
            <select 
              id="expires_in_hours" 
              v-model="createForm.expires_in_hours"
              required
            >
              <option value="1">1小时</option>
              <option value="24">24小时</option>
              <option value="168">7天</option>
              <option value="720">30天</option>
            </select>
          </div>
          
          <div class="form-actions">
            <button 
              type="button" 
              @click="showCreateDialog = false"
              class="cancel-btn"
            >
              取消
            </button>
            <button 
              type="submit" 
              class="submit-btn"
              :disabled="creating"
            >
              {{ creating ? '生成中...' : '生成' }}
            </button>
          </div>
        </form>
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
import { authService, type InviteCode } from '@/services/authService'

// 响应式数据
const inviteCodes = ref<InviteCode[]>([])
const loading = ref(false)
const showCreateDialog = ref(false)
const creating = ref(false)
const revoking = ref<number | null>(null)
const successMessage = ref('')
const errorMessage = ref('')

// 创建表单
const createForm = ref({
  expires_in_hours: 24
})

// 生命周期
onMounted(() => {
  loadInviteCodes()
})

// 方法
const loadInviteCodes = async () => {
  loading.value = true
  try {
    inviteCodes.value = await authService.getMyInviteCodes()
  } catch (error: any) {
    showError(error.message)
  } finally {
    loading.value = false
  }
}

const createInviteCode = async () => {
  creating.value = true
  try {
    const newCode = await authService.generateInviteCode(createForm.value.expires_in_hours)
    inviteCodes.value.unshift(newCode)
    showCreateDialog.value = false
    showSuccess('邀请码生成成功!')
    
    // 自动复制到剪贴板
    await copyToClipboard(newCode.code)
  } catch (error: any) {
    showError(error.message)
  } finally {
    creating.value = false
  }
}

const revokeCode = async (codeId: number) => {
  if (!confirm('确定要撤销这个邀请码吗？')) return
  
  revoking.value = codeId
  try {
    await authService.revokeInviteCode(codeId)
    await loadInviteCodes() // 重新加载列表
    showSuccess('邀请码已撤销')
  } catch (error: any) {
    showError(error.message)
  } finally {
    revoking.value = null
  }
}

const copyToClipboard = async (text: string) => {
  try {
    await navigator.clipboard.writeText(text)
    showSuccess('邀请码已复制到剪贴板')
  } catch (error) {
    // 降级处理
    const textArea = document.createElement('textarea')
    textArea.value = text
    document.body.appendChild(textArea)
    textArea.select()
    document.execCommand('copy')
    document.body.removeChild(textArea)
    showSuccess('邀请码已复制到剪贴板')
  }
}

// 工具函数
const isExpired = (code: InviteCode): boolean => {
  return new Date(code.expires_at) < new Date()
}

const getStatusText = (code: InviteCode): string => {
  if (code.is_used) return '已使用'
  if (isExpired(code)) return '已过期'
  return '有效'
}

const getStatusClass = (code: InviteCode): string => {
  if (code.is_used) return 'used'
  if (isExpired(code)) return 'expired'
  return 'valid'
}

const formatDate = (dateStr: string): string => {
  return new Date(dateStr).toLocaleString('zh-CN')
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
.invite-code-manager {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.manager-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
  padding-bottom: 15px;
  border-bottom: 2px solid #e1e5e9;
}

.manager-header h3 {
  margin: 0;
  color: #2c3e50;
  font-size: 24px;
}

.create-btn {
  background: #007bff;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  transition: background-color 0.2s;
}

.create-btn:hover:not(:disabled) {
  background: #0056b3;
}

.create-btn:disabled {
  background: #6c757d;
  cursor: not-allowed;
}

.loading, .empty-state {
  text-align: center;
  padding: 40px;
  color: #6c757d;
  font-size: 16px;
}

.codes-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
  gap: 20px;
}

.code-card {
  border: 1px solid #e1e5e9;
  border-radius: 8px;
  padding: 20px;
  background: white;
  transition: box-shadow 0.2s;
}

.code-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.code-card.expired {
  border-color: #dc3545;
  background: #fff5f5;
}

.code-card.used {
  border-color: #6c757d;
  background: #f8f9fa;
}

.code-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.code-text {
  font-family: 'Courier New', monospace;
  font-size: 18px;
  font-weight: bold;
  color: #007bff;
  background: #f8f9fa;
  padding: 8px 12px;
  border-radius: 4px;
  border: 1px solid #e1e5e9;
}

.code-actions {
  display: flex;
  gap: 8px;
}

.copy-btn, .revoke-btn {
  background: none;
  border: 1px solid #e1e5e9;
  border-radius: 4px;
  padding: 6px 8px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
}

.copy-btn:hover {
  background: #e9ecef;
  border-color: #adb5bd;
}

.revoke-btn:hover:not(:disabled) {
  background: #fff5f5;
  border-color: #dc3545;
}

.revoke-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.code-info {
  font-size: 14px;
}

.info-row {
  display: flex;
  margin-bottom: 8px;
}

.info-row .label {
  min-width: 80px;
  color: #6c757d;
  font-weight: 500;
}

.status {
  font-weight: 500;
}

.status.valid {
  color: #28a745;
}

.status.expired {
  color: #dc3545;
}

.status.used {
  color: #6c757d;
}

/* 模态框样式 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 8px;
  padding: 24px;
  width: 400px;
  max-width: 90vw;
}

.modal-content h4 {
  margin: 0 0 20px 0;
  color: #2c3e50;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
  color: #495057;
}

.form-group select {
  width: 100%;
  padding: 10px;
  border: 1px solid #ced4da;
  border-radius: 4px;
  font-size: 14px;
}

.form-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
}

.cancel-btn {
  background: none;
  border: 1px solid #ced4da;
  padding: 10px 20px;
  border-radius: 4px;
  cursor: pointer;
  color: #6c757d;
}

.cancel-btn:hover {
  background: #f8f9fa;
}

.submit-btn {
  background: #007bff;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 4px;
  cursor: pointer;
}

.submit-btn:hover:not(:disabled) {
  background: #0056b3;
}

.submit-btn:disabled {
  background: #6c757d;
  cursor: not-allowed;
}

/* 提示消息样式 */
.success-toast, .error-toast {
  position: fixed;
  top: 20px;
  right: 20px;
  padding: 12px 20px;
  border-radius: 4px;
  color: white;
  font-weight: 500;
  z-index: 1001;
  animation: slideIn 0.3s ease;
}

.success-toast {
  background: #28a745;
}

.error-toast {
  background: #dc3545;
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
  .codes-grid {
    grid-template-columns: 1fr;
  }
  
  .manager-header {
    flex-direction: column;
    gap: 15px;
    align-items: stretch;
  }
  
  .code-header {
    flex-direction: column;
    gap: 10px;
    align-items: flex-start;
  }
  
  .code-actions {
    align-self: flex-end;
  }
}
</style>