import { createRouter, createWebHistory, RouteRecordRaw } from "vue-router";
import HomeView from "../views/HomeView.vue";
import DatasetMarketplaceView from "../views/DatasetMarketplaceView.vue";
import RoleSelectionView from "../views/RoleSelectionView.vue";
import LoginView from "../views/LoginView.vue";
import RawQuestionManagementView from "../views/RawQuestionManagementView.vue";
import DataImportView from "../views/DataImportView.vue";
import DatabaseView from "../views/DatabaseView.vue";
import ManualStdQaCreationView from "../views/ManualStdQaCreationView.vue";

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
    path: "/data-import",
    name: "DataImport",
    component: DataImportView,
    meta: { requiresAuth: true, role: 'admin' }
  },
  {
    path: "/database/:id",
    name: "DatabaseView",
    component: DatabaseView,
    meta: { requiresAuth: true },
    props: true
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
  {
    path: "/manual-std-qa-creation/:datasetId",
    name: "ManualStdQaCreation",
    component: ManualStdQaCreationView,
    meta: { requiresAuth: true, role: 'admin' },
    props: true
  },
  {
    path: "/database-version-create/:datasetId",
    name: "DatabaseVersionCreate",
    component: () => import("../views/DatabaseVersionCreateView.vue"),
    meta: { requiresAuth: true, role: 'admin' },
    props: true
  },
  {
    path: "/database-version-edit/:datasetId/:versionId/:workId",
    name: "DatabaseVersionEdit",
    component: () => import("../views/DatabaseVersionEditView.vue"),
    meta: { requiresAuth: true, role: 'admin' },
    props: true
  },
  {
    path: "/llm-marketplace",
    name: "LLMMarketplace",
    component: () => import("../views/LLMMarketplaceView.vue"),
    meta: { requiresAuth: true, role: 'user' }
  },
  {
    path: "/llm-evaluation/:datasetId?",
    name: "LLMEvaluation", 
    component: () => import("../views/LLMEvaluationView.vue"),
    meta: { requiresAuth: true, role: 'user' },
    props: true
  },
  // {
  //   path: "/llm-task-evaluation",
  //   name: "LLMTaskEvaluation",
  //   component: () => import("../views/LLMTaskEvaluationView.vue"),
  //   meta: { requiresAuth: true, role: 'user' }
  // },
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
    // if (!user || !token) {
    //   // 清除可能残留的认证信息
    //   localStorage.removeItem('userInfo')
    //   localStorage.removeItem('token')
    //   next({ name: 'RoleSelection' })
    //   return
    // }

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
