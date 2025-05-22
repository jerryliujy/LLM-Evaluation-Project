<template>
  <nav>
    <router-link to="/raw-question-management">原始问题管理</router-link>
  </nav>
  <router-view />
</template>

<style>
nav {
  padding: 15px;
  text-align: center;
  background-color: #f8f9fa;
  border-bottom: 1px solid #dee2e6;
}
nav a {
  font-weight: bold;
  color: #2c3e50;
  margin: 0 10px;
  text-decoration: none;
}
nav a.router-link-exact-active {
  color: #42b983;
}
</style>
