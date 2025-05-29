import { createRouter, createWebHistory, RouteRecordRaw } from "vue-router";
import HomeView from "../views/HomeView.vue";
import RawQuestionManagementView from "../views/RawQuestionManagementView.vue"; // Import the new view
import DataImportView from "../views/DataImportView.vue"; // Import data import view

const routes: Array<RouteRecordRaw> = [
  {
    path: "/",
    name: "home",
    component: HomeView,
  },
  {
    path: "/about",
    name: "about",
    component: () =>
      import(/* webpackChunkName: "about" */ "../views/AboutView.vue"),
  },
  {
    // Add new route for raw question management
    path: "/raw-question-management",
    name: "RawQuestionManagement",
    component: RawQuestionManagementView,
    // meta: { requiresAuth: true, roles: ['admin'] } // Example for future auth
  },
  {
    // Add new route for data import
    path: "/data-import",
    name: "DataImport",
    component: DataImportView,
    // meta: { requiresAuth: true, roles: ['admin'] } // Example for future auth
  },
  // Define 'CreateRawQuestion' route here when implementing creation
];

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes,
});

export default router;
