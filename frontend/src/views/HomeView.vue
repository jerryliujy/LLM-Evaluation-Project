<template>
  <div class="home">
    <div class="hero-section">
      <h1>复旦大学数据库管理系统</h1>
      <p class="hero-description">
        专业的问答数据管理平台，支持数据导入、查看、编辑和管理
      </p>
    </div>

    <div class="features-section">
      <div class="feature-grid">
        <div class="feature-card">
          <div class="feature-icon">📊</div>
          <h3>数据库管理</h3>
          <p>查看和管理原始问题、答案、专家答案等数据表</p>
          <router-link to="/database-view" class="feature-link">进入管理 →</router-link>
        </div>

        <div class="feature-card">
          <div class="feature-icon">📁</div>
          <h3>数据导入</h3>
          <p>支持JSON格式的数据文件导入，实时预览数据内容</p>
          <router-link to="/data-import" class="feature-link">开始导入 →</router-link>
        </div>

        <div class="feature-card">
          <div class="feature-icon">🔍</div>
          <h3>CRUD操作</h3>
          <p>完整的增删改查功能，支持批量操作和数据恢复</p>
          <router-link to="/database-view" class="feature-link">立即使用 →</router-link>
        </div>

        <div class="feature-card">
          <div class="feature-icon">📈</div>
          <h3>实时统计</h3>
          <p>实时显示数据库状态和统计信息</p>
          <router-link to="/data-import" class="feature-link">查看状态 →</router-link>
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
            <p>使用数据导入功能上传JSON文件</p>
          </div>
        </div>
        <div class="step">
          <div class="step-number">3</div>
          <div class="step-content">
            <h4>管理数据</h4>
            <p>通过数据库管理界面进行增删改查操作</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
// 使用 Composition API
</script>

<style scoped>
.home {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
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
  text-decoration: none;
  font-weight: 600;
  transition: color 0.2s;
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
