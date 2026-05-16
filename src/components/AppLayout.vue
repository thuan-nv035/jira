<script setup>
import { computed } from "vue";
import { useRouter, useRoute } from "vue-router";
import { KanbanSquare, LogOut, Search } from "lucide-vue-next";
import NotificationBell from "./NotificationBell.vue";
import { clearAuth, getUser } from "../utils/storage";

const router = useRouter();
const route = useRoute()
const user = computed(() => getUser());
const projectId = computed(() => route.params.id)
function logout() {
  clearAuth();
  router.push({ name: "login" });
}
</script>

<template>
  <div class="min-h-screen bg-slate-50">
    <header
      class="sticky top-0 z-30 border-b border-slate-200 bg-white/90 backdrop-blur-xl"
    >
      <div
        class="mx-auto flex max-w-7xl items-center justify-between px-5 py-3"
      >
        <RouterLink to="/projects" class="flex items-center gap-3">
          <div
            class="flex h-10 w-10 items-center justify-center rounded-2xl bg-slate-900 text-white shadow-sm"
          >
            <KanbanSquare class="h-5 w-5" />
          </div>
          <div>
            <p class="text-sm font-black tracking-tight text-slate-950">
              Jira Clone
            </p>
            <!-- <p class="text-xs text-slate-500">FastAPI + Vue + Socket</p> -->
          </div>
        </RouterLink>

        <!-- <div class="hidden w-full max-w-md items-center gap-2 rounded-2xl border border-slate-200 bg-slate-50 px-3 py-2 md:flex">
          <Search class="h-4 w-4 text-slate-400" />
          <input class="w-full bg-transparent text-sm outline-none placeholder:text-slate-400" placeholder="Search projects, issues..." />
        </div> -->

        <div class="flex items-center gap-3">
          <router-link
            :to="`/projects/${projectId}/backlog`"
            class="rounded-2xl border border-slate-200 px-4 py-2 text-sm font-black text-slate-600 transition hover:bg-slate-100"
          >
            Backlog
          </router-link>
          <router-link
            to="/my-tasks"
            class="rounded-2xl px-4 py-2 text-sm font-black text-slate-600 hover:bg-slate-100"
          >
            My Tasks
          </router-link>
          <NotificationBell />
          <div class="hidden text-right sm:block">
            <p class="text-sm font-bold text-slate-900">
              {{ user?.full_name || "User" }}
            </p>
            <p class="text-xs text-slate-500">{{ user?.email }}</p>
          </div>

          <button @click="logout" class="btn-secondary px-3" title="Logout">
            <LogOut class="h-4 w-4" />
          </button>
        </div>
      </div>
    </header>

    <main class="mx-auto max-w-7xl px-5 py-6">
      <slot />
    </main>
  </div>
</template>
