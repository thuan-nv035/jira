<script setup>
import { computed, onMounted, reactive, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import {
  ArrowLeft,
  Layers3,
  ListTodo,
  RefreshCcw,
  Search,
} from "lucide-vue-next";
import {
  backlogApi,
  getErrorMessage,
  projectApi,
  sprintApi,
} from "../services/api";
import BacklogIssueItem from "../components/backlog/BacklogIssueItem.vue";
import SprintPanel from "../components/backlog/SprintPanel.vue";
import { useToast } from "../composables/useToast";

const route = useRoute();
const router = useRouter();
const toast = useToast();

const projectId = computed(() => Number(route.params.id));

const project = ref(null);
const sprints = ref([]);
const backlogIssues = ref([]);
const sprintIssuesMap = reactive({});
const sprintLoadingMap = reactive({});

const loading = ref(false);
const backlogLoading = ref(false);
const sprintLoading = ref(false);
const movingIssueId = ref(null);
const error = ref("");
const draggedIssue = ref(null);
const activeDropZone = ref("");

const filters = reactive({
  sprintStatus: "",
  keyword: "",
});

const filteredSprints = computed(() => {
  let result = sprints.value;

  if (filters.sprintStatus) {
    result = result.filter((sprint) => sprint.status === filters.sprintStatus);
  }

  const keyword = filters.keyword.trim().toLowerCase();

  if (keyword) {
    result = result.filter((sprint) => {
      const name = sprint.name?.toLowerCase() || "";
      const goal = sprint.goal?.toLowerCase() || "";

      return name.includes(keyword) || goal.includes(keyword);
    });
  }

  return result;
});

const activeSprints = computed(() => {
  return sprints.value.filter((sprint) => sprint.status !== "COMPLETED");
});

const totalSprintIssues = computed(() => {
  return Object.values(sprintIssuesMap).reduce((total, issues) => {
    return total + (issues?.length || 0);
  }, 0);
});

async function loadProject() {
  project.value = await projectApi.get(projectId.value);
}

async function loadSprints() {
  sprintLoading.value = true;

  try {
    sprints.value = await sprintApi.list(projectId.value);

    await Promise.all(
      sprints.value.map((sprint) => loadSprintIssues(sprint.id)),
    );
  } catch (err) {
    error.value = getErrorMessage(err);
    toast.error(error.value);
  } finally {
    sprintLoading.value = false;
  }
}

async function loadBacklog() {
  backlogLoading.value = true;

  try {
    backlogIssues.value = await backlogApi.listBacklog(projectId.value, {
      limit: 200,
      offset: 0,
    });
  } catch (err) {
    error.value = getErrorMessage(err);
    toast.error(error.value);
  } finally {
    backlogLoading.value = false;
  }
}

async function loadSprintIssues(sprintId) {
  sprintLoadingMap[sprintId] = true;

  try {
    sprintIssuesMap[sprintId] = await backlogApi.listSprintIssues(
      projectId.value,
      sprintId,
      {
        limit: 200,
        offset: 0,
      },
    );
  } catch (err) {
    error.value = getErrorMessage(err);
    toast.error(error.value);
  } finally {
    sprintLoadingMap[sprintId] = false;
  }
}

async function loadPage() {
  loading.value = true;
  error.value = "";

  try {
    await loadProject();
    await Promise.all([loadBacklog(), loadSprints()]);
  } catch (err) {
    error.value = getErrorMessage(err);
    toast.error(error.value);
  } finally {
    loading.value = false;
  }
}

function openIssue(issue) {
  router.push({
    path: `/projects/${issue.project_id}`,
    query: {
      issueId: issue.id,
    },
  });
}

async function moveIssueToSprint({ issue, sprintId }) {
  if (!issue || !sprintId) return;

  movingIssueId.value = issue.id;

  try {
    await sprintApi.updateIssueSprint(issue.id, sprintId);

    backlogIssues.value = backlogIssues.value.filter(
      (item) => Number(item.id) !== Number(issue.id)
    );

    Object.keys(sprintIssuesMap).forEach((key) => {
      sprintIssuesMap[key] = (sprintIssuesMap[key] || []).filter(
        (item) => Number(item.id) !== Number(issue.id)
      );
    });

    const nextIssue = {
      ...issue,
      sprint_id: sprintId
    };

    if (!sprintIssuesMap[sprintId]) {
      sprintIssuesMap[sprintId] = [];
    }

    sprintIssuesMap[sprintId] = [
      nextIssue,
      ...sprintIssuesMap[sprintId]
    ];

    toast.success("Issue moved to sprint");
  } catch (err) {
    error.value = getErrorMessage(err);
    toast.error(error.value);

    await Promise.all([
      loadBacklog(),
      loadSprints()
    ]);
  } finally {
    movingIssueId.value = null;
  }
}

async function moveIssueToBacklog(issue) {
  if (!issue) return;

  movingIssueId.value = issue.id;

  try {
    await sprintApi.updateIssueSprint(issue.id, null);

    Object.keys(sprintIssuesMap).forEach((key) => {
      sprintIssuesMap[key] = (sprintIssuesMap[key] || []).filter(
        (item) => Number(item.id) !== Number(issue.id)
      );
    });

    const nextIssue = {
      ...issue,
      sprint_id: null
    };

    backlogIssues.value = [
      nextIssue,
      ...backlogIssues.value.filter(
        (item) => Number(item.id) !== Number(issue.id)
      )
    ];

    toast.success("Issue moved to backlog");
  } catch (err) {
    error.value = getErrorMessage(err);
    toast.error(error.value);

    await Promise.all([
      loadBacklog(),
      loadSprints()
    ]);
  } finally {
    movingIssueId.value = null;
  }
}

async function startSprint(sprint) {
  try {
    await sprintApi.start(sprint.id);
    await loadSprints();
    toast.success("Sprint started");
  } catch (err) {
    error.value = getErrorMessage(err);
    toast.error(error.value);
  }
}

async function completeSprint(sprint) {
  if (!window.confirm(`Complete sprint "${sprint.name}"?`)) return;

  try {
    await sprintApi.complete(sprint.id);
    await loadSprints();
    toast.success("Sprint completed");
  } catch (err) {
    error.value = getErrorMessage(err);
    toast.error(error.value);
  }
}

function clearFilters() {
  filters.sprintStatus = "";
  filters.keyword = "";
}

function onIssueDragStart(issue) {
  draggedIssue.value = issue;
}

function onIssueDragEnd() {
  draggedIssue.value = null;
  activeDropZone.value = "";
}

function setActiveDropZone(zone) {
  if (!draggedIssue.value) return;
  activeDropZone.value = zone;
}

async function dropIssueToSprint(sprint) {
  if (!draggedIssue.value || !sprint) return;

  const issue = draggedIssue.value;

  if (Number(issue.sprint_id) === Number(sprint.id)) {
    onIssueDragEnd();
    return;
  }

  await moveIssueToSprint({
    issue,
    sprintId: sprint.id,
  });

  onIssueDragEnd();
}

async function dropIssueToBacklog() {
  if (!draggedIssue.value) return;

  const issue = draggedIssue.value;

  if (!issue.sprint_id) {
    onIssueDragEnd();
    return;
  }

  await moveIssueToBacklog(issue);

  onIssueDragEnd();
}

onMounted(loadPage);
</script>

<template>
  <main class="min-h-screen bg-slate-50 px-6 py-8">
    <div class="mx-auto max-w-7xl">
      <button
        type="button"
        class="mb-6 inline-flex items-center gap-2 text-sm font-bold text-slate-500 transition hover:text-slate-900"
        @click="router.back()"
      >
        <ArrowLeft class="h-4 w-4" />
        Back
      </button>

      <section
        class="mb-6 rounded-3xl border border-slate-200 bg-white p-6 shadow-sm"
      >
        <div class="flex flex-wrap items-center justify-between gap-4">
          <div class="flex items-center gap-3">
            <div
              class="flex h-12 w-12 items-center justify-center rounded-2xl bg-slate-900 text-white"
            >
              <Layers3 class="h-6 w-6" />
            </div>

            <div>
              <h1 class="text-2xl font-black text-slate-950">Backlog</h1>

              <p class="text-sm font-medium text-slate-500">
                {{ project?.name || "Project" }} · Manage backlog and sprint
                planning
              </p>
            </div>
          </div>

          <button
            type="button"
            class="rounded-2xl border border-slate-200 px-4 py-2 text-sm font-black text-slate-600 transition hover:bg-slate-100"
            :disabled="loading"
            @click="loadPage"
          >
            <RefreshCcw class="mr-2 inline h-4 w-4" />
            Refresh
          </button>
        </div>
      </section>

      <section class="mb-6 grid gap-4 md:grid-cols-3">
        <div class="rounded-3xl border border-slate-100 bg-white p-5 shadow-sm">
          <p class="text-sm font-black uppercase tracking-wide text-slate-400">
            Backlog issues
          </p>
          <p class="mt-2 text-3xl font-black text-slate-950">
            {{ backlogIssues.length }}
          </p>
        </div>

        <div
          class="rounded-3xl border border-blue-100 bg-blue-50 p-5 shadow-sm"
        >
          <p class="text-sm font-black uppercase tracking-wide text-blue-600">
            Sprints
          </p>
          <p class="mt-2 text-3xl font-black text-blue-700">
            {{ sprints.length }}
          </p>
        </div>

        <div
          class="rounded-3xl border border-violet-100 bg-violet-50 p-5 shadow-sm"
        >
          <p class="text-sm font-black uppercase tracking-wide text-violet-600">
            Sprint issues
          </p>
          <p class="mt-2 text-3xl font-black text-violet-700">
            {{ totalSprintIssues }}
          </p>
        </div>
      </section>

      <section
        class="mb-6 rounded-3xl border border-slate-200 bg-white p-5 shadow-sm"
      >
        <div class="mb-4 flex items-center gap-2">
          <Search class="h-5 w-5 text-slate-400" />
          <h2 class="font-black text-slate-900">Sprint filters</h2>
        </div>

        <div class="grid gap-3 md:grid-cols-[1fr_auto_auto]">
          <input
            v-model="filters.keyword"
            type="text"
            placeholder="Search sprint name or goal..."
            class="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm font-bold text-slate-700 outline-none transition focus:border-blue-400"
          />

          <select
            v-model="filters.sprintStatus"
            class="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm font-bold text-slate-700 outline-none transition focus:border-blue-400"
          >
            <option value="">All statuses</option>
            <option value="PLANNED">PLANNED</option>
            <option value="ACTIVE">ACTIVE</option>
            <option value="COMPLETED">COMPLETED</option>
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
        class="mb-6 rounded-2xl border border-rose-100 bg-rose-50 p-4 text-sm font-bold text-rose-700"
      >
        {{ error }}
      </div>

      <div
        v-if="loading"
        class="rounded-3xl bg-white p-6 text-sm font-semibold text-slate-500 shadow-sm"
      >
        Loading backlog...
      </div>

      <div v-else class="grid gap-6 xl:grid-cols-[420px_1fr]">
        <section
          class="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm"
        >
          <div class="mb-4 flex items-center justify-between gap-3">
            <div class="flex items-center gap-2">
              <ListTodo class="h-5 w-5 text-slate-500" />
              <h2 class="font-black text-slate-950">Backlog</h2>
            </div>

            <span
              class="rounded-full bg-slate-100 px-3 py-1 text-xs font-black text-slate-500"
            >
              {{ backlogIssues.length }} issue(s)
            </span>
          </div>

          <div
            v-if="backlogLoading"
            class="rounded-2xl bg-slate-50 p-4 text-sm font-semibold text-slate-500"
          >
            Loading backlog issues...
          </div>

          <div
            v-else-if="backlogIssues.length === 0"
            class="rounded-2xl bg-slate-50 p-6 text-center text-sm font-semibold text-slate-400"
          >
            No backlog issues.
          </div>

          <div
            class="min-h-[220px] rounded-3xl border border-dashed transition"
            :class="
              activeDropZone === 'backlog'
                ? 'border-blue-300 bg-blue-50/60 p-3'
                : 'border-transparent'
            "
            @dragover.prevent="setActiveDropZone('backlog')"
            @drop.prevent="dropIssueToBacklog"
          >
            <div
              v-if="backlogLoading"
              class="rounded-2xl bg-slate-50 p-4 text-sm font-semibold text-slate-500"
            >
              Loading backlog issues...
            </div>

            <div
              v-else-if="backlogIssues.length === 0"
              class="rounded-2xl border border-dashed border-slate-200 bg-slate-50 p-6 text-center text-sm font-semibold text-slate-400"
            >
              Drop issues here to move them back to backlog.
            </div>

            <div v-else class="max-h-[760px] space-y-3 overflow-y-auto pr-1">
              <BacklogIssueItem
                v-for="issue in backlogIssues"
                :key="issue.id"
                :issue="issue"
                :sprints="activeSprints"
                :can-edit="true"
                mode="backlog"
                @open="openIssue"
                @move-to-sprint="moveIssueToSprint"
                @drag-start="onIssueDragStart"
                @drag-end="onIssueDragEnd"
              />
            </div>
          </div>
        </section>

        <section class="space-y-6">
          <SprintPanel
            v-for="sprint in filteredSprints"
            :key="sprint.id"
            :sprint="sprint"
            :issues="sprintIssuesMap[sprint.id] || []"
            :all-sprints="activeSprints"
            :loading="Boolean(sprintLoadingMap[sprint.id])"
            :can-edit="true"
            @refresh="loadSprintIssues(sprint.id)"
            @open-issue="openIssue"
            @move-to-sprint="moveIssueToSprint"
            @move-to-backlog="moveIssueToBacklog"
            @start="startSprint"
            @complete="completeSprint"
            @drop-issue="dropIssueToSprint"
            @drag-start="onIssueDragStart"
            @drag-end="onIssueDragEnd"
          />

          <div
            v-if="filteredSprints.length === 0"
            class="rounded-3xl border border-slate-200 bg-white p-10 text-center shadow-sm"
          >
            <p class="font-black text-slate-700">No sprints found</p>

            <p class="mt-1 text-sm text-slate-400">
              Create sprints from your project board first.
            </p>
          </div>
        </section>
      </div>
    </div>
  </main>
</template>
