import { createRouter, createWebHistory, RouteRecordRaw } from "vue-router";
import HomeView from "../views/HomeView.vue";
import DataImportView from "../views/DataImportView.vue";

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
    path: "/data-import",
    name: "DataImport",
    component: DataImportView,
  },
  {
    path: "/database-view",
    name: "DatabaseView",
    component: () => 
      import(/* webpackChunkName: "database" */ "../views/DatabaseView.vue"),
  },
];

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes,
});

export default router;
