import { createRouter, createWebHistory } from "vue-router";
import { getToken } from "../utils/storage";

const routes = [
  {
    path: "/",
    redirect: "/projects",
  },
  {
    path: "/login",
    name: "login",
    component: () => import("../views/LoginView.vue"),
    meta: { guest: true },
  },
  {
    path: "/register",
    name: "register",
    component: () => import("../views/RegisterView.vue"),
    meta: { guest: true },
  },
  {
    path: "/projects",
    name: "projects",
    component: () => import("../views/DashboardView.vue"),
    meta: { requiresAuth: true },
  },
  {
    path: "/projects/:id/board",
    name: "board",
    component: () => import("../views/BoardView.vue"),
    meta: { requiresAuth: true },
  },
  {
    path: "/notifications",
    name: "notifications",
    component: () => import("../views/NotificationsView.vue"),
    meta: { requiresAuth: true },
  },
  {
    path: "/my-tasks",
    name: "my-tasks",
    component: () => import("../views/MyTasksView.vue"),
    meta: { requiresAuth: true },
  },
  {
    path: "/projects/:id/backlog",
    name: "project-backlog",
    component: () => import("../views/BacklogView.vue"),
    meta: { requiresAuth: true },
  },
  {
    path: "/projects/:id/sprints/:sprintId",
    name: "sprint-board",
    component: () => import("../views/SprintBoardView.vue"),
    meta: { requiresAuth: true },
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

router.beforeEach((to) => {
  const isLoggedIn = Boolean(getToken());

  if (to.meta.requiresAuth && !isLoggedIn) {
    return {
      path: "/login",
      query: {
        redirect: to.fullPath,
      },
    };
  }

  if (to.meta.guestOnly && isLoggedIn) {
    return "/projects";
  }

  return true;
});

export default router;
