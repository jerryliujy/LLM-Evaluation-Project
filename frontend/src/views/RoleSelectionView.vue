<template>
  <div class="role-selection-container">
    <div class="role-selection-card">
      <div class="header">
        <h1>欢迎使用复旦大学数据库管理系统</h1>
        <p class="subtitle">请选择您的身份角色</p>
      </div>

      <div class="roles-grid">
        <div class="role-card" @click="selectRole('admin')">
          <div class="role-icon">👨‍💼</div>
          <h3>数据库管理者</h3>
          <p>管理数据库、导入数据、进行CRUD操作</p>
          <div class="role-features">
            <span class="feature">• 数据库管理</span>
            <span class="feature">• 数据导入</span>
            <span class="feature">• 完整权限</span>
          </div>
        </div>

        <div class="role-card" @click="selectRole('user')">
          <div class="role-icon">👤</div>
          <h3>普通使用者</h3>
          <p>浏览和查看公开的数据库内容</p>
          <div class="role-features">
            <span class="feature">• 浏览数据库</span>
            <span class="feature">• 查看数据</span>
            <span class="feature">• 只读权限</span>
          </div>
        </div>

        <div class="role-card disabled" @click="selectRole('expert')">
          <div class="role-icon">👨‍🏫</div>
          <h3>专家用户</h3>
          <p>提供专业答案和评审内容</p>
          <div class="role-features">
            <span class="feature">• 专家答案</span>
            <span class="feature">• 内容评审</span>
            <span class="feature">• 即将推出</span>
          </div>
          <div class="coming-soon">即将推出</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()

const selectRole = (role: 'admin' | 'user' | 'expert') => {
  if (role === 'expert') {
    // 专家角色暂未实现
    return
  }
  
  // 将角色信息存储到 localStorage
  localStorage.setItem('userRole', role)
  
  // 根据角色跳转到相应的登录页面
  router.push({ 
    name: 'Login', 
    query: { role } 
  })
}
</script>

<style scoped>
.role-selection-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.role-selection-card {
  background: white;
  border-radius: 16px;
  padding: 40px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
  max-width: 900px;
  width: 100%;
}

.header {
  text-align: center;
  margin-bottom: 40px;
}

.header h1 {
  color: #333;
  margin: 0 0 10px 0;
  font-size: 2.2em;
  font-weight: 700;
}

.subtitle {
  color: #666;
  margin: 0;
  font-size: 1.1em;
}

.roles-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 24px;
}

.role-card {
  border: 2px solid #e1e5e9;
  border-radius: 12px;
  padding: 30px 20px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
  background: white;
}

.role-card:hover:not(.disabled) {
  border-color: #007bff;
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 123, 255, 0.15);
}

.role-card.disabled {
  opacity: 0.6;
  cursor: not-allowed;
  background: #f8f9fa;
}

.role-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.role-card h3 {
  color: #333;
  margin: 0 0 12px 0;
  font-size: 1.4em;
}

.role-card p {
  color: #666;
  margin: 0 0 20px 0;
  line-height: 1.6;
}

.role-features {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.feature {
  color: #007bff;
  font-size: 14px;
  font-weight: 500;
}

.coming-soon {
  position: absolute;
  top: 10px;
  right: 10px;
  background: #ffc107;
  color: #fff;
  font-size: 12px;
  padding: 4px 8px;
  border-radius: 12px;
  font-weight: bold;
}

@media (max-width: 768px) {
  .role-selection-card {
    padding: 20px;
  }
  
  .header h1 {
    font-size: 1.8em;
  }
  
  .roles-grid {
    grid-template-columns: 1fr;
  }
}
</style>
