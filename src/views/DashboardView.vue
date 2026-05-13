<script setup>
import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { FolderKanban, Plus, Users } from "lucide-vue-next";
import AppLayout from "../components/AppLayout.vue";
import EmptyState from "../components/EmptyState.vue";
import ProjectFormModal from "../components/ProjectFormModal.vue";
import { getErrorMessage, projectApi } from "../services/api";

const router = useRouter();
const projects = ref([]);
const loading = ref(true);
const error = ref("");
const showCreate = ref(false);

async function loadProjects() {
  loading.value = true;
  error.value = "";
  try {
    projects.value = await projectApi.list();
  } catch (err) {
    error.value = getErrorMessage(err);
  } finally {
    loading.value = false;
  }
}

function openProject(project) {
  router.push({ name: "board", params: { id: project.id } });
}

function onProjectCreated(project) {
  showCreate.value = false;
  projects.value = [project, ...projects.value];
  openProject(project);
}

onMounted(loadProjects);
</script>

<template>
  <AppLayout>
    <div class="mb-6 flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
      <div>
        <p class="text-sm font-black uppercase tracking-[0.18em] text-blue-600">Workspace</p>
        <h1 class="mt-2 text-3xl font-black tracking-tight text-slate-950">Projects</h1>
        <p class="mt-2 text-sm text-slate-500">Quản lý các project Jira clone của bạn.</p>
      </div>
      <button class="btn-primary" @click="showCreate = true">
        <Plus class="h-4 w-4" />
        New project
      </button>
    </div>

    <p v-if="error" class="mb-4 rounded-xl bg-rose-50 px-4 py-3 text-sm font-medium text-rose-700">{{ error }}</p>

    <div v-if="loading" class="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
      <div v-for="i in 6" :key="i" class="h-44 animate-pulse rounded-3xl bg-white"></div>
    </div>

    <EmptyState v-else-if="projects.length === 0" title="No projects yet" description="Tạo project đầu tiên để bắt đầu quản lý task theo bảng Kanban.">
      <button class="btn-primary" @click="showCreate = true">Create project</button>
    </EmptyState>

    <div v-else class="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
      <article
        v-for="project in projects"
        :key="project.id"
        class="group cursor-pointer overflow-hidden rounded-3xl border border-slate-200 bg-white p-5 shadow-sm transition hover:-translate-y-1 hover:shadow-soft"
        @click="openProject(project)"
      >
        <div class="mb-5 flex items-start justify-between gap-3">
          <div class="flex h-12 w-12 items-center justify-center rounded-2xl bg-slate-900 text-white">
            <FolderKanban class="h-6 w-6" />
          </div>
          <span class="rounded-full bg-blue-50 px-3 py-1 text-xs font-black text-blue-700">{{ project.key }}</span>
        </div>
        <h2 class="text-xl font-black tracking-tight text-slate-950 group-hover:text-blue-700">{{ project.name }}</h2>
        <p class="mt-2 line-clamp-2 min-h-10 text-sm leading-5 text-slate-500">
          {{ project.description || 'No description yet.' }}
        </p>
        <div class="mt-5 flex items-center justify-between border-t border-slate-100 pt-4 text-xs font-semibold text-slate-500">
          <span class="flex items-center gap-1.5"><Users class="h-4 w-4" /> Owner #{{ project.owner_id }}</span>
          <span>{{ new Date(project.created_at).toLocaleDateString() }}</span>
        </div>
      </article>
    </div>

    <ProjectFormModal v-if="showCreate" @close="showCreate = false" @created="onProjectCreated" />
  </AppLayout>
</template>
