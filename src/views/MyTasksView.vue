<script setup>
import { computed, onMounted, reactive, ref } from "vue";
import { useRouter } from "vue-router";
import {
  ArrowLeft,
  CalendarDays,
  CheckSquare,
  ListTodo,
  RefreshCcw,
  Search,
  AlertTriangle
} from "lucide-vue-next";
import { getErrorMessage, meApi, projectApi } from "../services/api";
import { formatDateTime } from "../utils/dateUtils";

const router = useRouter();

const loading = ref(false);
const error = ref("");
const issues = ref([]);
const projects = ref([]);

const filters = reactive({
  project_id: "",
  priority: "",
  issue_type: "",
  overdue: "",
  due_soon: "",
  sort_by: "updated_at",
  order: "desc"
});

const overdueCount = computed(() => {
  return issues.value.filter((issue) => issue.is_overdue).length;
});

const dueSoonCount = computed(() => {
  const now = new Date();
  const soon = new Date();
  soon.setDate(now.getDate() + 3);

  return issues.value.filter((issue) => {
    if (!issue.due_date || issue.is_overdue) return false;

    const due = new Date(issue.due_date);

    return due >= now && due <= soon;
  }).length;
});

async function loadProjects() {
  try {
    projects.value = await projectApi.list();
  } catch (err) {
    error.value = getErrorMessage(err);
  }
}

function buildParams() {
  return {
    project_id: filters.project_id ? Number(filters.project_id) : "",
    priority: filters.priority,
    issue_type: filters.issue_type,
    overdue:
      filters.overdue === ""
        ? ""
        : filters.overdue === "true",
    due_soon:
      filters.due_soon === ""
        ? ""
        : filters.due_soon === "true",
    sort_by: filters.sort_by,
    order: filters.order
  };
}

async function loadMyTasks() {
  loading.value = true;
  error.value = "";

  try {
    issues.value = await meApi.issues(buildParams());
  } catch (err) {
    error.value = getErrorMessage(err);
  } finally {
    loading.value = false;
  }
}

function clearFilters() {
  filters.project_id = "";
  filters.priority = "";
  filters.issue_type = "";
  filters.overdue = "";
  filters.due_soon = "";
  filters.sort_by = "updated_at";
  filters.order = "desc";

  loadMyTasks();
}

function openIssue(issue) {
  router.push({
    path: `/projects/${issue.project_id}`,
    query: {
      issueId: issue.id
    }
  });
}

function getPriorityClass(priority) {
  const value = String(priority || "").toUpperCase();

  if (value === "URGENT") return "bg-rose-50 text-rose-700 border-rose-100";
  if (value === "HIGH") return "bg-orange-50 text-orange-700 border-orange-100";
  if (value === "MEDIUM") return "bg-blue-50 text-blue-700 border-blue-100";
  if (value === "LOW") return "bg-emerald-50 text-emerald-700 border-emerald-100";

  return "bg-slate-50 text-slate-700 border-slate-100";
}

function checklistPercent(issue) {
  const total = Number(issue.checklist_total || 0);
  const done = Number(issue.checklist_done || 0);

  if (total === 0) return 0;

  return Math.round((done * 100) / total);
}

onMounted(async () => {
  await Promise.all([
    loadProjects(),
    loadMyTasks()
  ]);
});
</script>

<template>
  <main class="min-h-screen bg-slate-50 px-6 py-8">
    <div class="mx-auto max-w-6xl">
      <button
        type="button"
        class="mb-6 inline-flex items-center gap-2 text-sm font-bold text-slate-500 transition hover:text-slate-900"
        @click="router.back()"
      >
        <ArrowLeft class="h-4 w-4" />
        Back
      </button>

      <section class="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
        <div class="mb-6 flex flex-wrap items-center justify-between gap-4">
          <div class="flex items-center gap-3">
            <div class="flex h-12 w-12 items-center justify-center rounded-2xl bg-slate-900 text-white">
              <ListTodo class="h-6 w-6" />
            </div>

            <div>
              <h1 class="text-2xl font-black text-slate-950">
                My Tasks
              </h1>
              <p class="text-sm font-medium text-slate-500">
                Issues assigned to you across all projects
              </p>
            </div>
          </div>

          <button
            type="button"
            class="rounded-2xl border border-slate-200 px-4 py-2 text-sm font-black text-slate-600 transition hover:bg-slate-100"
            :disabled="loading"
            @click="loadMyTasks"
          >
            <RefreshCcw class="mr-2 inline h-4 w-4" />
            Refresh
          </button>
        </div>

        <div class="mb-6 grid gap-4 md:grid-cols-3">
          <div class="rounded-3xl border border-slate-100 bg-slate-50 p-4">
            <p class="text-sm font-black uppercase tracking-wide text-slate-400">
              Total assigned
            </p>
            <p class="mt-2 text-3xl font-black text-slate-950">
              {{ issues.length }}
            </p>
          </div>

          <div class="rounded-3xl border border-rose-100 bg-rose-50 p-4">
            <p class="text-sm font-black uppercase tracking-wide text-rose-500">
              Overdue
            </p>
            <p class="mt-2 text-3xl font-black text-rose-700">
              {{ overdueCount }}
            </p>
          </div>

          <div class="rounded-3xl border border-amber-100 bg-amber-50 p-4">
            <p class="text-sm font-black uppercase tracking-wide text-amber-600">
              Due soon
            </p>
            <p class="mt-2 text-3xl font-black text-amber-700">
              {{ dueSoonCount }}
            </p>
          </div>
        </div>

        <section class="mb-6 rounded-3xl border border-slate-200 bg-slate-50 p-4">
          <div class="mb-4 flex items-center gap-2">
            <Search class="h-5 w-5 text-slate-400" />
            <h2 class="font-black text-slate-900">
              Filters
            </h2>
          </div>

          <div class="grid gap-3 md:grid-cols-2 xl:grid-cols-7">
            <select
              v-model="filters.project_id"
              class="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm font-bold text-slate-700 outline-none"
              @change="loadMyTasks"
            >
              <option value="">All projects</option>
              <option
                v-for="project in projects"
                :key="project.id"
                :value="project.id"
              >
                {{ project.name }}
              </option>
            </select>

            <select
              v-model="filters.priority"
              class="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm font-bold text-slate-700 outline-none"
              @change="loadMyTasks"
            >
              <option value="">All priorities</option>
              <option value="LOW">LOW</option>
              <option value="MEDIUM">MEDIUM</option>
              <option value="HIGH">HIGH</option>
              <option value="URGENT">URGENT</option>
            </select>

            <select
              v-model="filters.issue_type"
              class="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm font-bold text-slate-700 outline-none"
              @change="loadMyTasks"
            >
              <option value="">All types</option>
              <option value="TASK">TASK</option>
              <option value="BUG">BUG</option>
              <option value="STORY">STORY</option>
            </select>

            <select
              v-model="filters.overdue"
              class="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm font-bold text-slate-700 outline-none"
              @change="loadMyTasks"
            >
              <option value="">Deadline</option>
              <option value="true">Overdue</option>
              <option value="false">Not overdue</option>
            </select>

            <select
              v-model="filters.due_soon"
              class="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm font-bold text-slate-700 outline-none"
              @change="loadMyTasks"
            >
              <option value="">Due soon</option>
              <option value="true">Due in 3 days</option>
            </select>

            <select
              v-model="filters.sort_by"
              class="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm font-bold text-slate-700 outline-none"
              @change="loadMyTasks"
            >
              <option value="updated_at">Updated</option>
              <option value="created_at">Created</option>
              <option value="due_date">Due date</option>
              <option value="priority">Priority</option>
              <option value="title">Title</option>
            </select>

            <button
              type="button"
              class="rounded-2xl bg-slate-900 px-4 py-3 text-sm font-black text-white"
              @click="clearFilters"
            >
              Clear
            </button>
          </div>
        </section>

        <div
          v-if="error"
          class="mb-4 rounded-2xl border border-rose-100 bg-rose-50 p-4 text-sm font-bold text-rose-700"
        >
          {{ error }}
        </div>

        <div
          v-if="loading"
          class="rounded-2xl bg-slate-50 p-5 text-sm font-semibold text-slate-500"
        >
          Loading your tasks...
        </div>

        <div
          v-else-if="issues.length === 0"
          class="rounded-3xl bg-slate-50 p-10 text-center"
        >
          <CheckSquare class="mx-auto mb-3 h-10 w-10 text-slate-300" />

          <p class="font-black text-slate-700">
            No assigned tasks
          </p>

          <p class="mt-1 text-sm text-slate-400">
            Tasks assigned to you will appear here.
          </p>
        </div>

        <div v-else class="space-y-3">
          <article
            v-for="issue in issues"
            :key="issue.id"
            class="cursor-pointer rounded-3xl border border-slate-100 bg-white p-5 shadow-sm transition hover:-translate-y-0.5 hover:border-blue-200 hover:shadow-md"
            @click="openIssue(issue)"
          >
            <div class="flex flex-wrap items-start justify-between gap-4">
              <div class="min-w-0">
                <div class="mb-2 flex flex-wrap items-center gap-2">
                  <span class="rounded-full bg-slate-100 px-3 py-1 text-xs font-black text-slate-600">
                    {{ issue.code }}
                  </span>

                  <span
                    class="rounded-full border px-3 py-1 text-xs font-black"
                    :class="getPriorityClass(issue.priority)"
                  >
                    {{ issue.priority }}
                  </span>

                  <span
                    v-if="issue.is_overdue"
                    class="inline-flex items-center gap-1 rounded-full bg-rose-50 px-3 py-1 text-xs font-black text-rose-700"
                  >
                    <AlertTriangle class="h-3.5 w-3.5" />
                    Overdue
                  </span>
                </div>

                <h2 class="text-base font-black text-slate-950">
                  {{ issue.title }}
                </h2>

                <p
                  v-if="issue.description"
                  class="mt-1 line-clamp-2 text-sm font-medium text-slate-500"
                >
                  {{ issue.description }}
                </p>

                <div
                  v-if="issue.labels && issue.labels.length > 0"
                  class="mt-3 flex flex-wrap gap-1.5"
                >
                  <span
                    v-for="label in issue.labels.slice(0, 4)"
                    :key="label.id"
                    class="rounded-full border px-2 py-1 text-[11px] font-black"
                    :style="{
                      borderColor: label.color,
                      color: label.color,
                      backgroundColor: `${label.color}14`
                    }"
                  >
                    {{ label.name }}
                  </span>
                </div>
              </div>

              <div class="min-w-[180px] text-right">
                <div
                  v-if="issue.due_date"
                  class="mb-2 inline-flex items-center gap-2 rounded-full bg-slate-50 px-3 py-1.5 text-xs font-black text-slate-600"
                >
                  <CalendarDays class="h-3.5 w-3.5" />
                  {{ formatDateTime(issue.due_date) }}
                </div>

                <div
                  v-if="issue.checklist_total > 0"
                  class="mt-2"
                >
                  <div class="mb-1 flex justify-between text-xs font-bold text-slate-400">
                    <span>Checklist</span>
                    <span>{{ issue.checklist_done }}/{{ issue.checklist_total }}</span>
                  </div>

                  <div class="h-2 overflow-hidden rounded-full bg-slate-100">
                    <div
                      class="h-full rounded-full bg-slate-900"
                      :style="{ width: `${checklistPercent(issue)}%` }"
                    ></div>
                  </div>
                </div>
              </div>
            </div>
          </article>
        </div>
      </section>
    </div>
  </main>
</template>