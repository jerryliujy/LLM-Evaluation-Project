<template>
  <div class="invite-code-join">
    <div class="join-container">
      <div class="join-header">
        <h3>加入专家团队</h3>
        <p>请输入管理员提供的邀请码以加入专家团队</p>
      </div>

      <form @submit.prevent="joinWithCode" class="join-form">
        <div class="form-group">
          <label for="invite_code">邀请码</label>
          <input
            id="invite_code"
            v-model="inviteCode"
            type="text"
            placeholder="请输入邀请码"
            required
            :disabled="joining"
            class="code-input"
          />
        </div>

        <button 
          type="submit" 
          class="join-btn"
          :disabled="joining || !inviteCode.trim()"
        >
          {{ joining ? '加入中...' : '加入团队' }}
        </button>
      </form>

      <!-- 成功消息 -->
      <div v-if="successMessage" class="success-message">
        <div class="message-icon">✅</div>
        <div class="message-content">
          <h4>加入成功！</h4>
          <p>{{ successMessage }}</p>
          <button @click="goToDashboard" class="dashboard-btn">
            前往专家控制台
          </button>
        </div>
      </div>

      <!-- 错误消息 -->
      <div v-if="errorMessage" class="error-message">
        <div class="message-icon">❌</div>
        <div class="message-content">
          <h4>加入失败</h4>
          <p>{{ errorMessage }}</p>
          <button @click="clearError" class="retry-btn">
            重试
          </button>
        </div>
      </div>

      <!-- 帮助信息 -->
      <div class="help-section">
        <h4>需要帮助？</h4>
        <ul>
          <li>请确保邀请码输入正确</li>
          <li>邀请码可能已过期，请联系管理员获取新的邀请码</li>
          <li>每个邀请码只能使用一次</li>
          <li>如果问题仍然存在，请联系系统管理员</li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { authService } from '@/services/authService'

const router = useRouter()
const route = useRoute()

// 响应式数据
const inviteCode = ref('')
const joining = ref(false)
const successMessage = ref('')
const errorMessage = ref('')

// 生命周期
onMounted(() => {
  // 从 URL 参数中获取邀请码
  const codeFromQuery = route.query.code as string
  if (codeFromQuery) {
    inviteCode.value = codeFromQuery
  }
})

// 方法
const joinWithCode = async () => {
  if (!inviteCode.value.trim()) return

  joining.value = true
  errorMessage.value = ''
  
  try {
    const result = await authService.joinWithInviteCode(inviteCode.value.trim())
    successMessage.value = result.message || '成功加入专家团队！您现在可以访问专家功能。'
    inviteCode.value = ''
  } catch (error: any) {
    errorMessage.value = error.message || '加入失败，请检查邀请码是否正确'
  } finally {
    joining.value = false
  }
}

const goToDashboard = () => {
  router.push('/expert-dashboard')
}

const clearError = () => {
  errorMessage.value = ''
}
</script>

<script lang="ts">
export default {
  name: 'InviteCodeJoin'
}
</script>

<style scoped>
.invite-code-join {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.join-container {
  background: white;
  border-radius: 12px;
  padding: 40px;
  width: 100%;
  max-width: 500px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
}

.join-header {
  text-align: center;
  margin-bottom: 40px;
}

.join-header h3 {
  color: #2c3e50;
  font-size: 28px;
  margin: 0 0 12px 0;
  font-weight: 600;
}

.join-header p {
  color: #6c757d;
  font-size: 16px;
  margin: 0;
  line-height: 1.5;
}

.join-form {
  margin-bottom: 30px;
}

.form-group {
  margin-bottom: 24px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
  color: #495057;
  font-size: 14px;
}

.code-input {
  width: 100%;
  padding: 16px;
  border: 2px solid #e1e5e9;
  border-radius: 8px;
  font-size: 16px;
  font-family: 'Courier New', monospace;
  text-align: center;
  letter-spacing: 2px;
  text-transform: uppercase;
  transition: border-color 0.2s, box-shadow 0.2s;
  box-sizing: border-box;
}

.code-input:focus {
  outline: none;
  border-color: #007bff;
  box-shadow: 0 0 0 3px rgba(0, 123, 255, 0.1);
}

.code-input:disabled {
  background: #f8f9fa;
  color: #6c757d;
  cursor: not-allowed;
}

.join-btn {
  width: 100%;
  background: linear-gradient(135deg, #007bff, #0056b3);
  color: white;
  border: none;
  padding: 16px;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.join-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, #0056b3, #004085);
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(0, 123, 255, 0.3);
}

.join-btn:disabled {
  background: #6c757d;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.success-message, .error-message {
  display: flex;
  align-items: flex-start;
  padding: 20px;
  border-radius: 8px;
  margin-bottom: 30px;
}

.success-message {
  background: #d4edda;
  border: 1px solid #c3e6cb;
}

.error-message {
  background: #f8d7da;
  border: 1px solid #f5c6cb;
}

.message-icon {
  font-size: 24px;
  margin-right: 16px;
  flex-shrink: 0;
}

.message-content {
  flex: 1;
}

.message-content h4 {
  margin: 0 0 8px 0;
  font-size: 16px;
}

.success-message h4 {
  color: #155724;
}

.error-message h4 {
  color: #721c24;
}

.message-content p {
  margin: 0 0 16px 0;
  font-size: 14px;
  line-height: 1.5;
}

.success-message p {
  color: #155724;
}

.error-message p {
  color: #721c24;
}

.dashboard-btn, .retry-btn {
  background: none;
  border: 2px solid;
  padding: 8px 16px;
  border-radius: 4px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.dashboard-btn {
  border-color: #28a745;
  color: #28a745;
}

.dashboard-btn:hover {
  background: #28a745;
  color: white;
}

.retry-btn {
  border-color: #dc3545;
  color: #dc3545;
}

.retry-btn:hover {
  background: #dc3545;
  color: white;
}

.help-section {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 24px;
  border-left: 4px solid #007bff;
}

.help-section h4 {
  color: #2c3e50;
  font-size: 16px;
  margin: 0 0 16px 0;
}

.help-section ul {
  margin: 0;
  padding-left: 20px;
  color: #6c757d;
}

.help-section li {
  margin-bottom: 8px;
  font-size: 14px;
  line-height: 1.5;
}

.help-section li:last-child {
  margin-bottom: 0;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .join-container {
    padding: 30px 20px;
    margin: 20px;
  }
  
  .join-header h3 {
    font-size: 24px;
  }
  
  .join-header p {
    font-size: 15px;
  }
  
  .code-input {
    padding: 14px;
    font-size: 15px;
  }
  
  .join-btn {
    padding: 14px;
    font-size: 15px;
  }
}

@media (max-width: 480px) {
  .invite-code-join {
    padding: 10px;
  }
  
  .join-container {
    padding: 24px 16px;
  }
  
  .message-icon {
    font-size: 20px;
    margin-right: 12px;
  }
  
  .help-section {
    padding: 20px 16px;
  }
}
</style>
