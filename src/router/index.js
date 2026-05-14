import { createRouter, createWebHistory } from "vue-router";
import { getToken } from "../utils/storage";

const routes = [
  {
    path: "/",
    redirect: "/projects"
  },
  {
    path: "/login",
    name: "login",
    component: () => import("../views/LoginView.vue"),
    meta: { guest: true }
  },
  {
    path: "/register",
    name: "register",
    component: () => import("../views/RegisterView.vue"),
    meta: { guest: true }
  },
  {
    path: "/projects",
    name: "projects",
    component: () => import("../views/DashboardView.vue"),
    meta: { requiresAuth: true }
  },
  {
    path: "/projects/:id/board",
    name: "board",
    component: () => import("../views/BoardView.vue"),
    meta: { requiresAuth: true }
  },
  {
    path: "/notifications",
    name: "notifications",
    component: () => import("../views/NotificationsView.vue"),
    meta: { requiresAuth: true }
  }
];

const router = createRouter({
  history: createWebHistory(),
  routes
});

router.beforeEach((to) => {
  const isLoggedIn = Boolean(getToken());
  if (to.meta.requiresAuth && !isLoggedIn) {
    return { name: "login" };
  }
  if (to.meta.guest && isLoggedIn) {
    return { name: "projects" };
  }
  return true;
});

export default router;
