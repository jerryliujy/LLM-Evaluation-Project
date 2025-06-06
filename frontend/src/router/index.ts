import { createRouter, createWebHistory, RouteRecordRaw } from "vue-router";
import HomeView from "../views/HomeView.vue";
import DatasetMarketplaceView from "../views/DatasetMarketplaceView.vue";
import RoleSelectionView from "../views/RoleSelectionView.vue";
import LoginView from "../views/LoginView.vue";
import RawQuestionManagementView from "../views/RawQuestionManagementView.vue";

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
    path: "/raw-question-management",
    name: "RawQuestionManagement",
    component: RawQuestionManagementView,
    meta: { requiresAuth: true, role: 'admin' }
  },
  {
    path: "/expert-dashboard",
    name: "ExpertDashboard",
    component: () => import("../views/ExpertDashboardView.vue"),
    meta: { requiresAuth: true, role: 'expert' }
  },
  {
    path: "/join-expert",
    name: "JoinExpert",
    component: () => import("../components/InviteCodeJoin.vue"),
    meta: { requiresAuth: true }
  },
];

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes,
});

// 路由守卫
router.beforeEach((to, from, next) => {
  const userInfo = localStorage.getItem('userInfo')
  const token = localStorage.getItem('token')
  let user = null
  
  try {
    user = userInfo ? JSON.parse(userInfo) : null
  } catch (error) {
    console.error('Error parsing userInfo from localStorage:', error)
    localStorage.removeItem('userInfo') // 清除损坏的数据
    user = null
  }
  
  // 检查是否需要认证
  if (to.meta.requiresAuth) {
    if (!user || !token) {
      // 清除可能残留的认证信息
      localStorage.removeItem('userInfo')
      localStorage.removeItem('token')
      next({ name: 'RoleSelection' })
      return
    }

    // 检查角色权限
    if (to.meta.role && user.role !== to.meta.role) {
      // 权限不足，根据用户角色跳转到合适的页面
      if (user.role === 'admin') {
        next({ name: 'Home' })
      } else if (user.role === 'user' || user.role === 'expert') {
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
