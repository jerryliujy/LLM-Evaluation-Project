import { createRouter, createWebHistory, RouteRecordRaw } from "vue-router";
import HomeView from "../views/HomeView.vue";
import DataImportView from "../views/DataImportView.vue";
import DatasetMarketplaceView from "../views/DatasetMarketplaceView.vue";
import RoleSelectionView from "../views/RoleSelectionView.vue";
import LoginView from "../views/LoginView.vue";

const routes: Array<RouteRecordRaw> = [
  {
    path: "/",
    name: "RoleSelection",
    component: RoleSelectionView,
  },
  {
    path: "/login",
    name: "Login",
    component: LoginView,
  },
  {
    path: "/home",
    name: "Home",
    component: HomeView,
    meta: { requiresAuth: true, role: 'admin' }
  },
  {
    path: "/about",
    name: "about",
    component: () =>
      import(/* webpackChunkName: "about" */ "../views/AboutView.vue"),
  },
  {
    path: "/marketplace",
    name: "DatasetMarketplace",
    component: DatasetMarketplaceView,
    meta: { requiresAuth: true }
  },
  {
    path: "/data-import",
    name: "DataImport",
    component: DataImportView,
    meta: { requiresAuth: true, role: 'admin' }
  },
  {
    path: "/database-view",
    name: "DatabaseView",
    component: () => 
      import(/* webpackChunkName: "database" */ "../views/DatabaseView.vue"),
    meta: { requiresAuth: true, role: 'admin' }
  },
];

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes,
});

// 路由守卫
router.beforeEach((to, from, next) => {
  const userInfo = localStorage.getItem('userInfo')
  const user = userInfo ? JSON.parse(userInfo) : null
  
  // 检查是否需要认证
  if (to.meta.requiresAuth) {
    // 检查角色权限
    if (to.meta.role && user.role !== to.meta.role) {
      // 权限不足，根据用户角色跳转到合适的页面
      if (user.role === 'admin') {
        next({ name: 'Home' })
      } else if (user.role === 'user') {
        next({ name: 'DatasetMarketplace' })
      } else {
        next({ name: 'RoleSelection' })
      }
      return
    }
  }
  
  next()
})

export default router;
