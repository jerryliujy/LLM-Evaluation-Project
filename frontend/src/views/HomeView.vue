<template>
  <div class="home">
    <!-- 用户信息和导航栏 -->
    <div class="user-header">
      <div class="user-info">
        <span class="welcome">欢迎，{{ userInfo?.username }}</span>
        <span class="role-badge">数据库管理者</span>
      </div>
      <div class="header-actions">
        <button @click="goToMarketplace" class="nav-btn">
          数据库市场
        </button>
        <button @click="logout" class="logout-btn">
          退出登录
        </button>
      </div>
    </div>

    <div class="hero-section">
      <h1>数据库管理控制台</h1>
      <p class="hero-description">
        管理和浏览数据库市场，创建和分享您的数据集
      </p>
    </div>

    <div class="features-section">
      <div class="feature-grid">
        <div class="feature-card">
          <div class="feature-icon">🏪</div>
          <h3>数据库市场</h3>
          <p>浏览和管理公开的数据库，分享您的数据集给其他用户</p>
          <button @click="goToMarketplace" class="feature-link">进入市场 →</button>
        </div>

        <div class="feature-card">
          <div class="feature-icon">📁</div>
          <h3>数据导入</h3>
          <p>支持JSON格式的数据文件导入，实时预览数据内容</p>
          <router-link to="/data-import" class="feature-link">开始导入 →</router-link>
        </div>

        <div class="feature-card">
          <div class="feature-icon">📊</div>
          <h3>我的数据库</h3>
          <p>管理您创建的所有数据库，设置访问权限和分享设置</p>
          <button @click="goToMyDatasets" class="feature-link">查看数据库 →</button>
        </div>

        <div class="feature-card">
          <div class="feature-icon">📈</div>
          <h3>数据统计</h3>
          <p>查看数据库使用统计，了解数据集的访问情况</p>
          <button @click="goToMarketplace" class="feature-link">查看统计 →</button>
        </div>
      </div>
    </div>

    <div class="quick-start">
      <h2>快速开始</h2>
      <div class="steps">
        <div class="step">
          <div class="step-number">1</div>
          <div class="step-content">
            <h4>准备数据</h4>
            <p>准备符合格式要求的JSON数据文件</p>
          </div>
        </div>
        <div class="step">
          <div class="step-number">2</div>
          <div class="step-content">
            <h4>导入数据</h4>
            <p>使用数据导入功能创建新的数据集</p>
          </div>
        </div>
        <div class="step">
          <div class="step-number">3</div>
          <div class="step-content">
            <h4>分享数据</h4>
            <p>在数据库市场中分享您的数据集</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

// 用户信息
const userInfo = ref<any>(null)

// 获取用户信息
onMounted(() => {
  const userInfoStr = localStorage.getItem('userInfo')
  if (userInfoStr) {
    userInfo.value = JSON.parse(userInfoStr)
  }
})

// 导航到数据库市场
const goToMarketplace = () => {
  router.push({ name: 'DatasetMarketplace' })
}

// 导航到我的数据库
const goToMyDatasets = () => {
  router.push({ name: 'DatasetMarketplace', query: { tab: 'my-datasets' } })
}

// 退出登录
const logout = () => {
  localStorage.removeItem('userInfo')
  localStorage.removeItem('userRole')
  router.push({ name: 'RoleSelection' })
}
</script>

<style scoped>
.home {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.user-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: white;
  padding: 15px 20px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  margin-bottom: 20px;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.welcome {
  color: #333;
  font-weight: 600;
}

.role-badge {
  background: #007bff;
  color: white;
  padding: 4px 12px;
  border-radius: 16px;
  font-size: 12px;
  font-weight: 600;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.nav-btn {
  background: #28a745;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
  font-weight: 500;
  transition: background-color 0.3s ease;
}

.nav-btn:hover {
  background: #218838;
}

.logout-btn {
  background: #dc3545;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
  font-weight: 500;
  transition: background-color 0.3s ease;
}

.logout-btn:hover {
  background: #c82333;
}

.hero-section {
  text-align: center;
  padding: 60px 0;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 12px;
  margin-bottom: 40px;
}

.hero-section h1 {
  font-size: 2.5em;
  margin: 0 0 20px 0;
  font-weight: 700;
}

.hero-description {
  font-size: 1.2em;
  margin: 0;
  opacity: 0.9;
}

.features-section {
  margin-bottom: 40px;
}

.feature-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 24px;
}

.feature-card {
  padding: 30px 20px;
  background: white;
  border: 1px solid #e1e5e9;
  border-radius: 12px;
  text-align: center;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.feature-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
  border-color: #007bff;
}

.feature-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.feature-card h3 {
  margin: 0 0 12px 0;
  color: #333;
  font-size: 1.4em;
}

.feature-card p {
  color: #666;
  margin: 0 0 20px 0;
  line-height: 1.6;
}

.feature-link {
  color: #007bff;
  background: none;
  border: none;
  font-weight: 600;
  font-size: inherit;
  cursor: pointer;
  transition: color 0.2s;
  text-decoration: none;
  padding: 0;
}

.feature-link:hover {
  color: #0056b3;
  text-decoration: underline;
}

.quick-start {
  background: #f8f9fa;
  padding: 40px;
  border-radius: 12px;
}

.quick-start h2 {
  text-align: center;
  margin: 0 0 30px 0;
  color: #333;
}

.steps {
  display: flex;
  justify-content: space-between;
  gap: 20px;
}

.step {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 15px;
}

.step-number {
  width: 40px;
  height: 40px;
  background: #007bff;
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  font-size: 18px;
  flex-shrink: 0;
}

.step-content h4 {
  margin: 0 0 8px 0;
  color: #333;
}

.step-content p {
  margin: 0;
  color: #666;
  font-size: 14px;
}

@media (max-width: 768px) {
  .hero-section h1 {
    font-size: 2em;
  }
  
  .hero-description {
    font-size: 1em;
  }
  
  .steps {
    flex-direction: column;
    gap: 30px;
  }
  
  .step {
    justify-content: center;
    text-align: center;
  }
}
</style>
