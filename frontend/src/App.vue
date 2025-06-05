<template>
  <nav>
    <div class="nav-section">
      <router-link to="/">首页</router-link>
      <router-link to="/marketplace">数据库市场</router-link>
      <router-link to="/raw-question-management">原始问题池</router-link>
    </div>
  </nav>
  <router-view />
</template>

<script setup lang="ts">
// 简化的App，移除专家相关功能
</script>

<style>
nav {
  padding: 15px;
  background-color: #f8f9fa;
  border-bottom: 1px solid #dee2e6;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.nav-section {
  display: flex;
  align-items: center;
  gap: 15px;
}

.expert-section {
  gap: 10px;
}

nav a {
  font-weight: bold;
  color: #2c3e50;
  text-decoration: none;
  padding: 8px 12px;
  border-radius: 4px;
  transition: background-color 0.2s;
}

nav a:hover {
  background-color: #e9ecef;
}

nav a.router-link-exact-active {
  color: #42b983;
  background-color: #e8f5e8;
}

.logout-button {
  background-color: #dc3545;
  color: white;
  border: none;
  padding: 8px 12px;
  border-radius: 4px;
  cursor: pointer;
  font-weight: bold;
  transition: background-color 0.2s;
}

.logout-button:hover {
  background-color: #c82333;
}
</style>
