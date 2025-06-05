<template>
  <div class="login-container">
    <div class="login-card">
      <div class="header">
        <h2>{{ isRegister ? '注册' : '登录' }} - {{ getRoleLabel() }}</h2>
        <p class="subtitle">{{ getRoleDescription() }}</p>
      </div>

      <form @submit.prevent="handleSubmit" class="login-form">
        <div class="form-group">
          <label for="username">用户名</label>
          <input
            id="username"
            v-model="form.username"
            type="text"
            required
            placeholder="请输入用户名"
            class="form-input"
          />
        </div>

        <div class="form-group">
          <label for="password">密码</label>
          <input
            id="password"
            v-model="form.password"
            type="password"
            required
            placeholder="请输入密码"
            class="form-input"
          />
        </div>

        <div v-if="isRegister" class="form-group">
          <label for="confirmPassword">确认密码</label>
          <input
            id="confirmPassword"
            v-model="form.confirmPassword"
            type="password"
            required
            placeholder="请再次输入密码"
            class="form-input"
          />
        </div>

        <div v-if="error" class="error-message">
          {{ error }}
        </div>

        <button 
          type="submit" 
          :disabled="loading" 
          class="submit-btn"
        >
          {{ loading ? '处理中...' : (isRegister ? '注册' : '登录') }}
        </button>
      </form>

      <div class="form-footer">
        <p>
          {{ isRegister ? '已有账户？' : '还没有账户？' }}
          <button @click="toggleMode" class="link-btn">
            {{ isRegister ? '立即登录' : '立即注册' }}
          </button>
        </p>
        
        <button @click="goBack" class="back-btn">
          ← 返回角色选择
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { authService } from '@/services/authService'

const route = useRoute()
const router = useRouter()

// 表单数据
const form = ref({
  username: '',
  password: '',
  confirmPassword: '',
  email: ''
})

// 状态
const isRegister = ref(false)
const loading = ref(false)
const error = ref('')

// 当前角色
const currentRole = computed(() => route.query.role as string || 'admin')

const getRoleLabel = (role?: string) => {
  const labels = {
    admin: '数据库管理者',
    user: '普通使用者',
    expert: '专家用户'
  }
  return labels[(role || currentRole.value) as keyof typeof labels] || '用户'
}

const getRoleDescription = () => {
  const descriptions = {
    admin: '登录后可以管理数据库、导入数据和进行完整的CRUD操作',
    user: '登录后可以浏览和查看公开的数据库内容',
    expert: '登录后可以提供专业答案和评审内容'
  }
  return descriptions[currentRole.value as keyof typeof descriptions] || ''
}

const toggleMode = () => {
  isRegister.value = !isRegister.value
  error.value = ''
  // 清空确认密码字段
  if (!isRegister.value) {
    form.value.confirmPassword = ''
    form.value.email = ''
  }
}

const validateForm = () => {
  if (!form.value.username.trim()) {
    error.value = '请输入用户名'
    return false
  }
  
  if (!form.value.password.trim()) {
    error.value = '请输入密码'
    return false
  }
  
  if (form.value.password.length < 6) {
    error.value = '密码长度至少6位'
    return false
  }
  
  if (isRegister.value) {
    if (form.value.password !== form.value.confirmPassword) {
      error.value = '两次输入的密码不一致'
      return false
    }
  }
  
  return true
}

const handleSubmit = async () => {
  error.value = ''
  
  if (!validateForm()) {
    return
  }
  
  loading.value = true
  
  try {
    if (isRegister.value) {
      // 注册
      const registerData = {
        username: form.value.username,
        password: form.value.password,
        role: currentRole.value as 'admin' | 'user' | 'expert'
      }
      
      const response = await authService.register(registerData)
        // 保存认证信息
      authService.saveToken(response.access_token, response.user)
      
      // 跳转到相应页面
      if (response.user.role === 'admin') {
        router.push({ name: 'Home' })
      } else if (response.user.role === 'expert') {
        router.push({ name: 'ExpertDashboard' })
      } else {
        router.push({ name: 'DatasetMarketplace' })
      }
      
    } else {
      // 登录
      const loginData = {
        username: form.value.username,
        password: form.value.password
      }
      
      const response = await authService.login(loginData)
      
      // 验证角色是否匹配
      if (response.user.role !== currentRole.value) {
        error.value = `此账户的角色是${getRoleLabel(response.user.role)}，请选择正确的角色登录`
        return
      }
      
      // 保存认证信息
      authService.saveToken(response.access_token, response.user)
        // 跳转到相应页面
      if (response.user.role === 'admin') {
        router.push({ name: 'Home' })
      } else if (response.user.role === 'expert') {
        router.push({ name: 'ExpertDashboard' })
      } else {
        router.push({ name: 'DatasetMarketplace' })
      }
    }
    
  } catch (err: any) {
    error.value = err.message || '操作失败，请重试'
  } finally {
    loading.value = false
  }
}

const goBack = () => {
  router.push({ name: 'RoleSelection' })
}

// 检查是否已登录
onMounted(async () => {
  if (authService.isAuthenticated()) {
    try {
      const user = await authService.getCurrentUser()
      if (user.role === currentRole.value) {        // 已登录且角色匹配，直接跳转
        if (user.role === 'admin') {
          router.push({ name: 'Home' })
        } else if (user.role === 'expert') {
          router.push({ name: 'ExpertDashboard' })
        } else {
          router.push({ name: 'DatasetMarketplace' })
        }
      }
    } catch (error) {
      // 认证过期或无效，清除token
      authService.clearToken()
    }
  }
})
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.login-card {
  background: white;
  border-radius: 16px;
  padding: 40px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
  max-width: 400px;
  width: 100%;
}

.header {
  text-align: center;
  margin-bottom: 30px;
}

.header h2 {
  color: #333;
  margin: 0 0 10px 0;
  font-size: 1.8em;
}

.subtitle {
  color: #666;
  margin: 0;
  font-size: 14px;
  line-height: 1.5;
}

.login-form {
  margin-bottom: 20px;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 5px;
  color: #333;
  font-weight: 500;
}

.form-input {
  width: 100%;
  padding: 12px;
  border: 2px solid #e1e5e9;
  border-radius: 8px;
  font-size: 16px;
  transition: border-color 0.3s ease;
  box-sizing: border-box;
}

.form-input:focus {
  outline: none;
  border-color: #007bff;
}

.error-message {
  background: #f8d7da;
  border: 1px solid #f5c6cb;
  color: #721c24;
  padding: 10px;
  border-radius: 4px;
  margin-bottom: 20px;
  font-size: 14px;
}

.submit-btn {
  width: 100%;
  padding: 12px;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.3s ease;
}

.submit-btn:hover:not(:disabled) {
  background: #0056b3;
}

.submit-btn:disabled {
  background: #6c757d;
  cursor: not-allowed;
}

.form-footer {
  text-align: center;
}

.form-footer p {
  color: #666;
  margin: 0 0 15px 0;
}

.link-btn {
  background: none;
  border: none;
  color: #007bff;
  cursor: pointer;
  text-decoration: underline;
  font-size: inherit;
}

.link-btn:hover {
  color: #0056b3;
}

.back-btn {
  background: none;
  border: 1px solid #6c757d;
  color: #6c757d;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.3s ease;
}

.back-btn:hover {
  background: #6c757d;
  color: white;
}

@media (max-width: 480px) {
  .login-card {
    padding: 20px;
  }
  
  .header h2 {
    font-size: 1.5em;
  }
}
</style>
