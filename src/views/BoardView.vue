<script setup>
import {
  computed,
  onBeforeUnmount,
  onMounted,
  reactive,
  ref,
  watch,
} from "vue";
import { useRoute, useRouter } from "vue-router";
import {
  ArrowLeft,
  Plus,
  RefreshCcw,
  UserPlus,
  Wifi,
  WifiOff,
  Activity,
} from "lucide-vue-next";
import AppLayout from "../components/AppLayout.vue";
import AddMemberModal from "../components/AddMemberModal.vue";
import BoardColumn from "../components/BoardColumn.vue";
import IssueDetailModal from "../components/IssueDetailModal.vue";
import IssueFormModal from "../components/IssueFormModal.vue";
import ProjectDashboard from "../components/ProjectDashboard.vue";
import {
  authApi,
  columnApi,
  epicApi,
  getErrorMessage,
  issueApi,
  labelApi,
  projectApi,
  sprintApi,
  activityApi
} from "../services/api";
import { createProjectSocket } from "../services/socket";

import { normalizeMember, getInitials, getAvatarColorClass } from "../utils/memberUtils";
import { formatDateTime as formatLogTime } from "../utils/dateUtils";
import { getActivityLabel, getActivityClass, getChangedFields } from "../utils/activityUtils";

const route = useRoute();
const router = useRouter();
const projectId = computed(() => Number(route.params.id));
const currentUser = ref(null);
const project = ref(null);
const columns = ref([]);
const issues = ref([]);
const members = ref([]);
const loading = ref(true);
const error = ref("");
const socketStatus = ref("disconnected");
const lastEvent = ref(null);

const showIssueForm = ref(false);
const selectedColumn = ref(null);
const selectedIssue = ref(null);
const showAddMember = ref(false);
const draggedIssue = ref(null);
let socket = null;
const projectLogs = ref([]);
const projectLogLoading = ref(false);
const projectLogLoadingMore = ref(false);
const projectLogHasMore = ref(true);
const PROJECT_LOG_LIMIT = 20;

const projectLabels = ref([]);
const labelLoading = ref(false);
const labelForm = reactive({
  name: "",
  color: "#2563eb",
});

const filterLoading = ref(false);

const filters = reactive({
  keyword: "",
  column_id: "",
  priority: "",
  issue_type: "",
  has_attachment: "",
  overdue: "",
  label_id: "",
  sort_by: "updated_at",
  order: "desc",
});

let filterTimer = null;

const epics = ref([]);
const sprints = ref([]);

const epicLoading = ref(false);
const sprintLoading = ref(false);

const epicForm = reactive({
  name: "",
  description: "",
  color: "#7c3aed",
});

const sprintForm = reactive({
  name: "",
  goal: "",
  start_date: "",
  end_date: "",
  status: "PLANNED",
});

const MAX_VISIBLE_AVATARS = 9;

const projectMemberAvatars = computed(() => {
  return members.value.map(normalizeMember).filter(Boolean);
});

const visibleProjectMembers = computed(() => {
  return projectMemberAvatars.value.slice(0, MAX_VISIBLE_AVATARS);
});

const hiddenProjectMemberCount = computed(() => {
  return Math.max(projectMemberAvatars.value.length - MAX_VISIBLE_AVATARS, 0);
});

const issueTotal = computed(() => issues.value.length);
const doneTotal = computed(() => {
  const doneColumn = columns.value.find((col) =>
    col.name.toUpperCase().includes("DONE"),
  );
  if (!doneColumn) return 0;
  return issues.value.filter((issue) => issue.column_id === doneColumn.id)
    .length;
});

function issuesByColumn(columnId) {
  return issues.value.filter((issue) => issue.column_id === columnId);
}

async function loadProjectMembers() {
  members.value = await projectApi.members(projectId.value);
}

async function loadBoard(options = {}) {
  const silent = options?.silent ?? false;
  if (!silent) {
    loading.value = true;
    error.value = "";
  }
  try {
    const [projectData, columnData] = await Promise.all([
      projectApi.get(projectId.value),
      columnApi.list(projectId.value),
    ]);
    project.value = projectData;
    columns.value = columnData;
    await refreshIssues({ silent: true });
  } catch (err) {
    error.value = getErrorMessage(err);
  } finally {
    loading.value = false;
  }
}

function openCreateIssue(column) {
  selectedColumn.value = column;
  showIssueForm.value = true;
}

function onIssueCreated(issue) {
  showIssueForm.value = false;
  issues.value = [...issues.value, issue];
}

function onIssueChanged(updatedIssue) {
  selectedIssue.value = updatedIssue;
  issues.value = issues.value.map((item) =>
    item.id === updatedIssue.id ? updatedIssue : item,
  );
}

function onIssueDeleted(issueId) {
  selectedIssue.value = null;
  issues.value = issues.value.filter((item) => item.id !== issueId);
}

function onDragIssue(issue) {
  draggedIssue.value = issue;
}

async function onDropIssue(column) {
  if (!draggedIssue.value || draggedIssue.value.column_id === column.id) return;
  const issue = draggedIssue.value;
  draggedIssue.value = null;

  const oldIssues = [...issues.value];
  const nextPosition = issuesByColumn(column.id).length;
  issues.value = issues.value.map((item) =>
    item.id === issue.id
      ? { ...item, column_id: column.id, position: nextPosition }
      : item,
  );

  try {
    const moved = await issueApi.move(projectId.value, issue.id, {
      column_id: column.id,
      position: nextPosition,
    });
    issues.value = issues.value.map((item) =>
      item.id === moved.id ? moved : item,
    );
  } catch (err) {
    issues.value = oldIssues;
    error.value = getErrorMessage(err);
  }
}

function onSocketMessage(payload) {
  lastEvent.value = payload;

  if (
    ["epic.created", "epic.updated", "epic.deleted"].includes(payload.event)
  ) {
    loadEpics({ silent: true });
    refreshIssues({ silent: true });
    return;
  }

  if (
    ["sprint.created", "sprint.updated", "sprint.deleted"].includes(
      payload.event,
    )
  ) {
    loadSprints({ silent: true });
    refreshIssues({ silent: true });
    return;
  }

  if (["issue.epic_updated", "issue.sprint_updated"].includes(payload.event)) {
    refreshIssues({ silent: true });
    window.dispatchEvent(
      new CustomEvent("jira-epic-sprint-refresh", { detail: payload.data }),
    );
    return;
  }

  if (payload.event === "activity.created") {
    window.dispatchEvent(
      new CustomEvent("jira-activity-refresh", { detail: payload.data }),
    );
  }
  if (
    ["label.created", "label.updated", "label.deleted"].includes(payload.event)
  ) {
    loadProjectLabels({ silent: true });
    refreshIssues({ silent: true });
    window.dispatchEvent(
      new CustomEvent("jira-label-refresh", { detail: payload.data }),
    );
    return;
  }

  if (["issue.label_added", "issue.label_removed"].includes(payload.event)) {
    window.dispatchEvent(
      new CustomEvent("jira-label-refresh", { detail: payload.data }),
    );
    refreshIssues({ silent: true });
    return;
  }

  if (
    [
      "issue.created",
      "issue.updated",
      "issue.moved",
      "issue.deleted",
      "checklist.created",
      "checklist.updated",
      "checklist.deleted",
      "activity.created",
      "member.added",
    ].includes(payload.event)
  ) {
    window.dispatchEvent(new CustomEvent("jira-dashboard-refresh"));
  }

  if (
    ["checklist.created", "checklist.updated", "checklist.deleted"].includes(
      payload.event,
    )
  ) {
    window.dispatchEvent(
      new CustomEvent("jira-checklist-refresh", { detail: payload.data }),
    );

    refreshIssues({ silent: true });
    return;
  }

  if (payload.event === "activity.created") {
    loadProjectLogs({
      reset: true,
      silent: true,
    });

    window.dispatchEvent(
      new CustomEvent("jira-activity-refresh", { detail: payload.data }),
    );
  }

  if (payload.event === "notification.created") {
    window.dispatchEvent(
      new CustomEvent("jira-notification-refresh", { detail: payload.data }),
    );
  }

  if (["attachment.uploaded", "attachment.deleted"].includes(payload.event)) {
    window.dispatchEvent(
      new CustomEvent("jira-attachment-refresh", { detail: payload.data }),
    );
  }

  if (payload.event === "issue.moved") {
    applyIssueMovedLocal(payload.data);
    return;
  }

  if (["member.role_updated", "member.removed"].includes(payload.event)) {
    loadProjectMembers();
    window.dispatchEvent(new CustomEvent("jira-dashboard-refresh"));
    return;
  }

  if (
    [
      "issue.created",
      "issue.updated",
      "issue.deleted",
      "comment.created",
      "attachment.uploaded",
      "attachment.deleted",
      "activity.created",
    ].includes(payload.event)
  ) {
    refreshIssues({ silent: true });
    return;
  }

  if (
    [
      "column.created",
      "column.updated",
      "column.deleted",
      "member.added",
      "notification.created",
    ].includes(payload.event)
  ) {
    loadBoard({ silent: true });
  }
}

function onMemberAdded(member) {
  showAddMember.value = false;
  members.value = [...members.value, member];
}

onBeforeUnmount(() => {
  clearTimeout(filterTimer);
  socket?.close();
});

function applyIssueMovedLocal(data) {
  const issueId = Number(data.issue_id);
  const newColumnId = Number(data.column_id);
  const newPosition = Number(data.position ?? 0);

  const index = issues.value.findIndex((issue) => Number(issue.id) === issueId);

  if (index === -1) {
    loadBoard({ silent: true });
    return;
  }

  issues.value[index] = {
    ...issues.value[index],
    column_id: newColumnId,
    position: newPosition,
  };

  issues.value = [...issues.value].sort((a, b) => {
    if (a.column_id !== b.column_id) {
      return a.column_id - b.column_id;
    }

    return a.position - b.position;
  });
}

const hasActiveIssueFilters = computed(() => {
  return Boolean(
    filters.keyword ||
    filters.column_id ||
    filters.priority ||
    filters.issue_type ||
    filters.overdue ||
    filters.label_id ||
    filters.has_attachment,
  );
});

function buildIssueSearchParams() {
  const params = {
    keyword: filters.keyword.trim(),
    column_id: filters.column_id ? Number(filters.column_id) : "",
    priority: filters.priority,
    issue_type: filters.issue_type,
    has_attachment:
      filters.has_attachment === "" ? "" : filters.has_attachment === "true",
    sort_by: filters.sort_by,
    order: filters.order,
    label_id: filters.label_id ? Number(filters.label_id) : "",
    overdue: filters.overdue === "" ? "" : filters.overdue === "true",
  };

  return params;
}

async function refreshIssues(options = {}) {
  const silent = options.silent ?? false;

  if (!projectId.value) return;

  if (!silent) {
    filterLoading.value = true;
  }

  try {
    if (hasActiveIssueFilters.value) {
      issues.value = await issueApi.search(
        projectId.value,
        buildIssueSearchParams(),
      );
    } else {
      issues.value = await issueApi.list(projectId.value);
    }
  } catch (err) {
    error.value = getErrorMessage(err);
  } finally {
    if (!silent) {
      filterLoading.value = false;
    }
  }
}

watch(
  filters,
  () => {
    clearTimeout(filterTimer);

    filterTimer = setTimeout(() => {
      refreshIssues({ silent: false });
    }, 350);
  },
  { deep: true },
);

function clearIssueFilters() {
  filters.keyword = "";
  filters.column_id = "";
  filters.priority = "";
  filters.issue_type = "";
  filters.has_attachment = "";
  filters.sort_by = "updated_at";
  filters.order = "desc";
  filters.overdue = "";
  filters.label_id = "";
}

async function loadProjectLogs(options = {}) {
  const reset = options.reset ?? false;
  const silent = options.silent ?? false;

  if (!projectId.value) return;

  if (projectLogLoading.value || projectLogLoadingMore.value) return;

  if (!reset && !projectLogHasMore.value) return;

  const offset = reset ? 0 : projectLogs.value.length;

  if (reset) {
    projectLogHasMore.value = true;

    if (!silent) {
      projectLogLoading.value = true;
    }
  } else {
    projectLogLoadingMore.value = true;
  }

  try {
    const data = await activityApi.listProjectLog(projectId.value, {
      limit: PROJECT_LOG_LIMIT,
      offset,
    });

    if (reset) {
      projectLogs.value = data;
    } else {
      const currentIds = new Set(projectLogs.value.map((item) => item.id));
      const newItems = data.filter((item) => !currentIds.has(item.id));

      projectLogs.value = [...projectLogs.value, ...newItems];
    }

    projectLogHasMore.value = data.length === PROJECT_LOG_LIMIT;
  } catch (err) {
    error.value = getErrorMessage(err);
  } finally {
    projectLogLoading.value = false;
    projectLogLoadingMore.value = false;
  }
}

function onProjectLogScroll(event) {
  const el = event.target;

  const nearBottom = el.scrollTop + el.clientHeight >= el.scrollHeight - 80;

  if (nearBottom) {
    loadProjectLogs({
      reset: false,
      silent: true,
    });
  }
}

const currentProjectMember = computed(() => {
  if (!currentUser.value) return null;

  return members.value
    .map(normalizeMember)
    .find((member) => Number(member.id) === Number(currentUser.value.id));
});

const currentProjectRole = computed(() => {
  if (!currentUser.value || !project.value) return "";

  if (Number(project.value.owner_id) === Number(currentUser.value.id)) {
    return "OWNER";
  }

  return currentProjectMember.value?.role || "";
});

const canManageMembers = computed(() => {
  return currentProjectRole.value === "OWNER";
});

const canManageColumns = computed(() => {
  return ["OWNER", "ADMIN"].includes(currentProjectRole.value);
});

const canEditIssues = computed(() => {
  return ["OWNER", "ADMIN", "MEMBER"].includes(currentProjectRole.value);
});

const isViewer = computed(() => {
  return currentProjectRole.value === "VIEWER";
});

async function loadCurrentUser() {
  try {
    currentUser.value = await authApi.me();
  } catch (err) {
    error.value = getErrorMessage(err);
  }
}

async function updateMemberRole(member, role) {
  if (!canManageMembers.value) return;

  try {
    await projectApi.updateMemberRole(projectId.value, member.id, role);
    await loadProjectMembers();

    window.dispatchEvent(new CustomEvent("jira-dashboard-refresh"));
  } catch (err) {
    error.value = getErrorMessage(err);
  }
}

async function removeProjectMember(member) {
  if (!canManageMembers.value) return;

  if (!confirm(`Remove ${member.full_name} from this project?`)) return;

  try {
    await projectApi.removeMember(projectId.value, member.id);
    await loadProjectMembers();

    window.dispatchEvent(new CustomEvent("jira-dashboard-refresh"));
  } catch (err) {
    error.value = getErrorMessage(err);
  }
}

function isProjectOwner(member) {
  return Number(project.value?.owner_id) === Number(member.id);
}

async function loadProjectLabels(options = {}) {
  const silent = options.silent ?? false;

  if (!projectId.value) return;

  if (!silent) {
    labelLoading.value = true;
  }

  try {
    projectLabels.value = await labelApi.listProjectLabels(projectId.value);
  } catch (err) {
    error.value = getErrorMessage(err);
  } finally {
    labelLoading.value = false;
  }
}

async function createProjectLabel() {
  const name = labelForm.name.trim();

  if (!name) return;

  try {
    await labelApi.create(projectId.value, {
      name,
      color: labelForm.color || "#2563eb",
    });

    labelForm.name = "";
    labelForm.color = "#2563eb";

    await loadProjectLabels({ silent: true });
  } catch (err) {
    error.value = getErrorMessage(err);
  }
}

async function deleteProjectLabel(label) {
  // if (!canEditIssues.value) return;
  if (!canManageColumns.value) return;
  if (!confirm(`Delete label "${label.name}"?`)) return;

  try {
    await labelApi.remove(label.id);
    projectLabels.value = projectLabels.value.filter(
      (item) => item.id !== label.id,
    );
    await refreshIssues({ silent: true });
  } catch (err) {
    error.value = getErrorMessage(err);
  }
}

async function openIssueFromQuery() {
  const issueId = Number(route.query.issueId);

  if (!issueId) return;

  let issue = issues.value.find((item) => Number(item.id) === issueId);

  if (!issue) {
    try {
      issue = await issueApi.get(projectId.value, issueId);
    } catch (err) {
      error.value = getErrorMessage(err);
      return;
    }
  }

  if (issue) {
    selectedIssue.value = issue;
  }
}

function closeIssueModal() {
  selectedIssue.value = null;

  router.replace({
    path: route.path,
    query: {
      ...route.query,
      issueId: undefined,
    },
  });
}

async function loadEpics(options = {}) {
  const silent = options.silent ?? false;

  if (!projectId.value) return;

  if (!silent) {
    epicLoading.value = true;
  }

  try {
    epics.value = await epicApi.list(projectId.value);
  } catch (err) {
    error.value = getErrorMessage(err);
  } finally {
    epicLoading.value = false;
  }
}

async function loadSprints(options = {}) {
  const silent = options.silent ?? false;

  if (!projectId.value) return;

  if (!silent) {
    sprintLoading.value = true;
  }

  try {
    sprints.value = await sprintApi.list(projectId.value);
  } catch (err) {
    error.value = getErrorMessage(err);
  } finally {
    sprintLoading.value = false;
  }
}

async function createEpic() {
  const name = epicForm.name.trim();

  if (!name) return;

  try {
    await epicApi.create(projectId.value, {
      name,
      description: epicForm.description || null,
      color: epicForm.color || "#7c3aed",
    });

    epicForm.name = "";
    epicForm.description = "";
    epicForm.color = "#7c3aed";

    await loadEpics({ silent: true });
  } catch (err) {
    error.value = getErrorMessage(err);
  }
}

async function createSprint() {
  const name = sprintForm.name.trim();

  if (!name) return;

  try {
    await sprintApi.create(projectId.value, {
      name,
      goal: sprintForm.goal || null,
      start_date: sprintForm.start_date
        ? new Date(sprintForm.start_date).toISOString()
        : null,
      end_date: sprintForm.end_date
        ? new Date(sprintForm.end_date).toISOString()
        : null,
      status: sprintForm.status || "PLANNED",
    });

    sprintForm.name = "";
    sprintForm.goal = "";
    sprintForm.start_date = "";
    sprintForm.end_date = "";
    sprintForm.status = "PLANNED";

    await loadSprints({ silent: true });
  } catch (err) {
    error.value = getErrorMessage(err);
  }
}

async function deleteEpic(epic) {
  if (!canEditIssues.value) return;

  if (!confirm(`Delete epic "${epic.name}"?`)) return;

  try {
    await epicApi.remove(epic.id);
    epics.value = epics.value.filter((item) => item.id !== epic.id);
    await refreshIssues({ silent: true });
  } catch (err) {
    error.value = getErrorMessage(err);
  }
}

async function deleteSprint(sprint) {
  if (!canEditIssues.value) return;

  if (!confirm(`Delete sprint "${sprint.name}"?`)) return;

  try {
    await sprintApi.remove(sprint.id);
    sprints.value = sprints.value.filter((item) => item.id !== sprint.id);
    await refreshIssues({ silent: true });
  } catch (err) {
    error.value = getErrorMessage(err);
  }
}

onMounted(async () => {
  await Promise.all([
    loadBoard(),
    loadCurrentUser(),
    loadProjectMembers(),
    loadProjectLogs({
      reset: true,
      silent: true,
    }),
    loadProjectLabels({ silent: true }),
    openIssueFromQuery(),
    loadEpics({ silent: true }),
    loadSprints({ silent: true }),
  ]);
  socket = createProjectSocket(projectId.value, onSocketMessage, (status) => {
    socketStatus.value = status;
  });
});

watch(
  () => route.query.issueId,
  () => {
    openIssueFromQuery();
  },
);
</script>

<template>
  <AppLayout>
    <div
      class="mb-5 flex flex-col gap-4 xl:flex-row xl:items-end xl:justify-between"
    >
      <div>
        <button
          class="mb-4 inline-flex items-center gap-2 text-sm font-bold text-slate-500 hover:text-slate-950"
          @click="router.push('/projects')"
        >
          <ArrowLeft class="h-4 w-4" /> Back to projects
        </button>
        <div class="flex flex-wrap items-center gap-3">
          <span
            class="rounded-full bg-blue-50 px-3 py-1 text-xs font-black text-blue-700"
            >{{ project?.key || "PROJECT" }}</span
          >
          <span
            :class="[
              'inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-black',
              socketStatus === 'connected'
                ? 'bg-emerald-50 text-emerald-700'
                : 'bg-slate-100 text-slate-500',
            ]"
          >
            <Wifi v-if="socketStatus === 'connected'" class="h-3.5 w-3.5" />
            <WifiOff v-else class="h-3.5 w-3.5" />
            {{ socketStatus }}
            <div
              v-if="projectMemberAvatars.length > 0"
              class="flex items-center gap-3 rounded-full bg-white px-3 py-2 shadow-sm ring-1 ring-slate-200"
            >
              <div class="flex -space-x-2">
                <div
                  v-for="(member, index) in visibleProjectMembers"
                  :key="member.id || index"
                  class="group relative"
                >
                  <div
                    class="flex h-9 w-9 items-center justify-center overflow-hidden rounded-full border-2 border-white text-xs font-black text-white shadow-sm ring-1 ring-slate-200 transition hover:z-10 hover:scale-110"
                    :class="
                      !member.avatar_url ? getAvatarColorClass(index) : ''
                    "
                    :title="member.full_name"
                  >
                    <img
                      v-if="member.avatar_url"
                      :src="member.avatar_url"
                      :alt="member.full_name"
                      class="h-full w-full object-cover"
                    />

                    <span v-else>
                      {{ getInitials(member.full_name) }}
                    </span>
                  </div>

                  <div
                    class="pointer-events-none absolute left-1/2 top-11 z-50 hidden w-max -translate-x-1/2 rounded-xl bg-slate-950 px-3 py-2 text-xs font-bold text-white shadow-xl group-hover:block"
                  >
                    {{ member.full_name }}
                    <div
                      v-if="member.email"
                      class="mt-0.5 text-[11px] font-medium text-slate-300"
                    >
                      {{ member.email }}
                    </div>
                  </div>
                </div>

                <div
                  v-if="hiddenProjectMemberCount > 0"
                  class="flex h-9 w-9 items-center justify-center rounded-full border-2 border-white bg-slate-100 text-xs font-black text-slate-600 shadow-sm ring-1 ring-slate-200"
                  :title="`${hiddenProjectMemberCount} more member(s)`"
                >
                  ...
                </div>
              </div>

              <span class="text-sm font-black text-slate-700">
                {{ projectMemberAvatars.length }}
              </span>
            </div>
          </span>
        </div>
        <h1 class="mt-3 text-3xl font-black tracking-tight text-slate-950">
          {{ project?.name || "Board" }}
        </h1>
        <p class="mt-2 max-w-2xl text-sm leading-6 text-slate-500">
          {{
            project?.description ||
            "Manage issues by dragging cards between columns."
          }}
        </p>
      </div>

      <div class="flex flex-wrap gap-3">
        <button class="btn-secondary" @click="loadBoard">
          <RefreshCcw class="h-4 w-4" /> Refresh
        </button>
        <button class="btn-secondary" @click="showAddMember = true">
          <UserPlus class="h-4 w-4" /> Add member
        </button>
        <button
          class="btn-secondary"
          @click="router.push(`/projects/${projectId}/dashboard`)"
        >
          <Activity class="h-4 w-4" /> Dashboard
        </button>
        <button
          v-if="canEditIssues"
          class="btn-primary"
          @click="openCreateIssue(columns[0])"
          :disabled="columns.length === 0"
        >
          <Plus class="h-4 w-4" /> Create issue
        </button>
      </div>
    </div>

    <div class="mb-5 grid gap-4 md:grid-cols-3">
      <div class="card p-5">
        <p class="text-sm font-semibold text-slate-500">Total issues</p>
        <p class="mt-2 text-3xl font-black text-slate-950">{{ issueTotal }}</p>
      </div>
      <div class="card p-5">
        <p class="text-sm font-semibold text-slate-500">Done</p>
        <p class="mt-2 text-3xl font-black text-slate-950">{{ doneTotal }}</p>
      </div>
      <div class="card p-5">
        <p class="text-sm font-semibold text-slate-500">Members</p>
        <p class="mt-2 text-3xl font-black text-slate-950">
          {{ members.length }}
        </p>
      </div>
    </div>

    <p
      v-if="error"
      class="mb-4 rounded-xl bg-rose-50 px-4 py-3 text-sm font-medium text-rose-700"
    >
      {{ error }}
    </p>

    <section
      class="mb-6 rounded-3xl border border-slate-200 bg-white p-5 shadow-sm"
    >
      <div class="mb-4 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 class="text-base font-black text-slate-950">Project Members</h2>
          <p class="text-sm text-slate-500">
            Manage member roles and permissions
          </p>
        </div>

        <span
          class="rounded-full px-3 py-1 text-xs font-black"
          :class="
            canManageMembers
              ? 'bg-slate-900 text-white'
              : 'bg-slate-100 text-slate-500'
          "
        >
          Your role: {{ currentProjectRole || "UNKNOWN" }}
        </span>
      </div>

      <div class="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
        <div
          v-for="member in projectMemberAvatars"
          :key="member.id"
          class="flex items-center justify-between gap-3 rounded-2xl border border-slate-100 bg-slate-50 p-4"
        >
          <div class="flex min-w-0 items-center gap-3">
            <div
              class="flex h-10 w-10 shrink-0 items-center justify-center overflow-hidden rounded-full text-xs font-black text-white"
              :class="
                !member.avatar_url ? getAvatarColorClass(member.id || 0) : ''
              "
            >
              <img
                v-if="member.avatar_url"
                :src="member.avatar_url"
                :alt="member.full_name"
                class="h-full w-full object-cover"
              />

              <span v-else>
                {{ getInitials(member.full_name) }}
              </span>
            </div>

            <div class="min-w-0">
              <p class="truncate text-sm font-black text-slate-900">
                {{ member.full_name }}
              </p>
              <p class="truncate text-xs text-slate-400">
                {{ member.email }}
              </p>
            </div>
          </div>

          <div class="flex shrink-0 items-center gap-2">
            <span
              v-if="isProjectOwner(member)"
              class="rounded-full bg-slate-900 px-3 py-1 text-xs font-black text-white"
            >
              OWNER
            </span>

            <select
              v-else
              :value="member.role"
              class="rounded-xl border border-slate-200 bg-white px-3 py-2 text-xs font-black text-slate-700 outline-none disabled:cursor-not-allowed disabled:bg-slate-100 disabled:text-slate-400"
              :disabled="!canManageMembers"
              @change="updateMemberRole(member, $event.target.value)"
            >
              <option value="ADMIN">ADMIN</option>
              <option value="MEMBER">MEMBER</option>
              <option value="VIEWER">VIEWER</option>
            </select>

            <button
              v-if="canManageMembers && !isProjectOwner(member)"
              type="button"
              class="rounded-xl border border-rose-200 px-3 py-2 text-xs font-black text-rose-500 transition hover:bg-rose-50"
              @click="removeProjectMember(member)"
            >
              Remove
            </button>
          </div>
        </div>
      </div>
    </section>

    <section
      class="mb-6 rounded-3xl border border-slate-200 bg-white p-5 shadow-sm"
    >
      <div class="mb-4 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 class="text-base font-black text-slate-950">Project Labels</h2>
          <p class="text-sm text-slate-500">
            Create and manage labels used by issues
          </p>
        </div>

        <span
          class="rounded-full bg-slate-100 px-3 py-1 text-xs font-black text-slate-500"
        >
          {{ projectLabels.length }} label(s)
        </span>
      </div>

      <form
        v-if="canEditIssues"
        class="mb-4 grid gap-3 md:grid-cols-[1fr_auto_auto]"
        @submit.prevent="createProjectLabel"
      >
        <input
          v-model="labelForm.name"
          type="text"
          placeholder="Label name, e.g. Frontend"
          class="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm font-bold text-slate-700 outline-none transition focus:border-blue-400 focus:bg-white"
        />

        <input
          v-model="labelForm.color"
          type="color"
          class="h-12 w-20 cursor-pointer rounded-2xl border border-slate-200 bg-white p-2"
        />

        <button
          type="submit"
          class="rounded-2xl bg-slate-900 px-5 py-3 text-sm font-black text-white transition hover:bg-slate-800 disabled:opacity-60"
          :disabled="!labelForm.name.trim()"
        >
          Add label
        </button>
      </form>

      <div
        v-if="labelLoading"
        class="rounded-2xl bg-slate-50 p-4 text-sm font-semibold text-slate-500"
      >
        Loading labels...
      </div>

      <div v-else class="flex flex-wrap gap-2">
        <div
          v-for="label in projectLabels"
          :key="label.id"
          class="group flex items-center gap-2 rounded-full border px-3 py-2 text-sm font-black"
          :style="{
            borderColor: label.color,
            color: label.color,
            backgroundColor: `${label.color}14`,
          }"
        >
          <span>{{ label.name }}</span>

          <button
            v-if="canEditIssues"
            type="button"
            class="hidden rounded-full px-1 text-xs group-hover:inline"
            title="Delete label"
            @click="deleteProjectLabel(label)"
          >
            ×
          </button>
        </div>

        <p
          v-if="projectLabels.length === 0"
          class="rounded-2xl bg-slate-50 p-4 text-sm font-semibold text-slate-500"
        >
          No labels yet.
        </p>
      </div>
    </section>
    <ProjectDashboard :project-id="projectId" />
    <section class="mb-6 grid gap-6 xl:grid-cols-2">
      <div class="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
        <div class="mb-4 flex items-center justify-between gap-3">
          <div>
            <h2 class="text-base font-black text-slate-950">Epics</h2>
            <p class="text-sm text-slate-500">
              Group related issues into larger goals
            </p>
          </div>

          <span
            class="rounded-full bg-violet-50 px-3 py-1 text-xs font-black text-violet-700"
          >
            {{ epics.length }} epic(s)
          </span>
        </div>

        <form
          v-if="canEditIssues"
          class="mb-4 grid gap-3 md:grid-cols-[1fr_auto_auto]"
          @submit.prevent="createEpic"
        >
          <input
            v-model="epicForm.name"
            type="text"
            placeholder="Epic name"
            class="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm font-bold outline-none focus:border-violet-400"
          />

          <input
            v-model="epicForm.color"
            type="color"
            class="h-12 w-20 cursor-pointer rounded-2xl border border-slate-200 bg-white p-2"
          />

          <button
            type="submit"
            class="rounded-2xl bg-violet-600 px-5 py-3 text-sm font-black text-white hover:bg-violet-700 disabled:opacity-60"
            :disabled="!epicForm.name.trim()"
          >
            Add epic
          </button>
        </form>

        <textarea
          v-if="canEditIssues"
          v-model="epicForm.description"
          rows="2"
          placeholder="Epic description..."
          class="mb-4 w-full resize-none rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm font-semibold outline-none focus:border-violet-400"
        ></textarea>

        <div
          v-if="epicLoading"
          class="rounded-2xl bg-slate-50 p-4 text-sm font-semibold text-slate-500"
        >
          Loading epics...
        </div>

        <div v-else class="space-y-3">
          <div
            v-for="epic in epics"
            :key="epic.id"
            class="flex items-center justify-between gap-3 rounded-2xl border border-slate-100 bg-slate-50 p-4"
          >
            <div class="min-w-0">
              <div class="flex items-center gap-2">
                <span
                  class="h-3 w-3 rounded-full"
                  :style="{ backgroundColor: epic.color }"
                ></span>

                <p class="truncate text-sm font-black text-slate-900">
                  {{ epic.name }}
                </p>
              </div>

              <p
                v-if="epic.description"
                class="mt-1 line-clamp-1 text-xs font-semibold text-slate-400"
              >
                {{ epic.description }}
              </p>
            </div>

            <button
              v-if="canEditIssues"
              type="button"
              class="rounded-xl border border-rose-200 px-3 py-2 text-xs font-black text-rose-500 hover:bg-rose-50"
              @click="deleteEpic(epic)"
            >
              Delete
            </button>
          </div>

          <p
            v-if="epics.length === 0"
            class="rounded-2xl bg-slate-50 p-4 text-sm font-semibold text-slate-500"
          >
            No epics yet.
          </p>
        </div>
      </div>

      <div class="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
        <div class="mb-4 flex items-center justify-between gap-3">
          <div>
            <h2 class="text-base font-black text-slate-950">Sprints</h2>
            <p class="text-sm text-slate-500">
              Plan issues into working cycles
            </p>
          </div>

          <span
            class="rounded-full bg-blue-50 px-3 py-1 text-xs font-black text-blue-700"
          >
            {{ sprints.length }} sprint(s)
          </span>
        </div>

        <form
          v-if="canEditIssues"
          class="mb-4 grid gap-3 md:grid-cols-2"
          @submit.prevent="createSprint"
        >
          <input
            v-model="sprintForm.name"
            type="text"
            placeholder="Sprint name"
            class="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm font-bold outline-none focus:border-blue-400"
          />

          <select
            v-model="sprintForm.status"
            class="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm font-bold outline-none focus:border-blue-400"
          >
            <option value="PLANNED">PLANNED</option>
            <option value="ACTIVE">ACTIVE</option>
            <option value="COMPLETED">COMPLETED</option>
          </select>

          <input
            v-model="sprintForm.start_date"
            type="datetime-local"
            class="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm font-bold outline-none focus:border-blue-400"
          />

          <input
            v-model="sprintForm.end_date"
            type="datetime-local"
            class="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm font-bold outline-none focus:border-blue-400"
          />

          <textarea
            v-model="sprintForm.goal"
            rows="2"
            placeholder="Sprint goal..."
            class="md:col-span-2 resize-none rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm font-semibold outline-none focus:border-blue-400"
          ></textarea>

          <button
            type="submit"
            class="md:col-span-2 rounded-2xl bg-blue-600 px-5 py-3 text-sm font-black text-white hover:bg-blue-700 disabled:opacity-60"
            :disabled="!sprintForm.name.trim()"
          >
            Add sprint
          </button>
        </form>

        <div
          v-if="sprintLoading"
          class="rounded-2xl bg-slate-50 p-4 text-sm font-semibold text-slate-500"
        >
          Loading sprints...
        </div>

        <div v-else class="space-y-3">
          <div
            v-for="sprint in sprints"
            :key="sprint.id"
            class="flex items-center justify-between gap-3 rounded-2xl border border-slate-100 bg-slate-50 p-4"
          >
            <div class="min-w-0">
              <div class="flex items-center gap-2">
                <span
                  class="rounded-full px-2 py-1 text-[11px] font-black"
                  :class="
                    sprint.status === 'ACTIVE'
                      ? 'bg-emerald-50 text-emerald-700'
                      : sprint.status === 'COMPLETED'
                        ? 'bg-slate-200 text-slate-600'
                        : 'bg-blue-50 text-blue-700'
                  "
                >
                  {{ sprint.status }}
                </span>

                <p class="truncate text-sm font-black text-slate-900">
                  {{ sprint.name }}
                </p>
              </div>

              <p
                v-if="sprint.goal"
                class="mt-1 line-clamp-1 text-xs font-semibold text-slate-400"
              >
                {{ sprint.goal }}
              </p>
            </div>

            <button
              v-if="canEditIssues"
              type="button"
              class="rounded-xl border border-rose-200 px-3 py-2 text-xs font-black text-rose-500 hover:bg-rose-50"
              @click="deleteSprint(sprint)"
            >
              Delete
            </button>
          </div>

          <p
            v-if="sprints.length === 0"
            class="rounded-2xl bg-slate-50 p-4 text-sm font-semibold text-slate-500"
          >
            No sprints yet.
          </p>
        </div>
      </div>
    </section>
    <section
      class="mb-6 rounded-3xl border border-slate-200 bg-white p-4 shadow-sm"
    >
      <div class="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
        <div>
          <label
            class="mb-1 block text-xs font-bold uppercase tracking-wide text-slate-400"
          >
            Search
          </label>

          <input
            v-model="filters.keyword"
            type="text"
            placeholder="Search title, code, description..."
            class="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-2.5 text-sm font-semibold text-slate-700 outline-none transition focus:border-blue-400 focus:bg-white"
          />
        </div>

        <div>
          <label
            class="mb-1 block text-xs font-bold uppercase tracking-wide text-slate-400"
          >
            Status
          </label>

          <select
            v-model="filters.column_id"
            class="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-2.5 text-sm font-semibold text-slate-700 outline-none transition focus:border-blue-400 focus:bg-white"
          >
            <option value="">All columns</option>
            <option
              v-for="column in columns"
              :key="column.id"
              :value="column.id"
            >
              {{ column.name }}
            </option>
          </select>
        </div>

        <div>
          <label
            class="mb-1 block text-xs font-bold uppercase tracking-wide text-slate-400"
          >
            Priority
          </label>

          <select
            v-model="filters.priority"
            class="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-2.5 text-sm font-semibold text-slate-700 outline-none transition focus:border-blue-400 focus:bg-white"
          >
            <option value="">All priorities</option>
            <option value="LOW">Low</option>
            <option value="MEDIUM">Medium</option>
            <option value="HIGH">High</option>
            <option value="URGENT">Urgent</option>
          </select>
        </div>

        <div>
          <label
            class="mb-1 block text-xs font-bold uppercase tracking-wide text-slate-400"
          >
            Type
          </label>

          <select
            v-model="filters.issue_type"
            class="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-2.5 text-sm font-semibold text-slate-700 outline-none transition focus:border-blue-400 focus:bg-white"
          >
            <option value="">All types</option>
            <option value="TASK">Task</option>
            <option value="BUG">Bug</option>
            <option value="STORY">Story</option>
          </select>
        </div>

        <div>
          <label
            class="mb-1 block text-xs font-bold uppercase tracking-wide text-slate-400"
          >
            Attachment
          </label>

          <select
            v-model="filters.has_attachment"
            class="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-2.5 text-sm font-semibold text-slate-700 outline-none transition focus:border-blue-400 focus:bg-white"
          >
            <option value="">All</option>
            <option value="true">Has files</option>
            <option value="false">No files</option>
          </select>
        </div>

        <div>
          <label
            class="mb-1 block text-xs font-bold uppercase tracking-wide text-slate-400"
          >
            Sort
          </label>

          <select
            v-model="filters.sort_by"
            class="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-2.5 text-sm font-semibold text-slate-700 outline-none transition focus:border-blue-400 focus:bg-white"
          >
            <option value="updated_at">Updated</option>
            <option value="created_at">Created</option>
            <option value="priority">Priority</option>
            <option value="title">Title</option>
            <option value="position">Position</option>
          </select>
        </div>
        <div>
          <label
            class="mb-1 block text-xs font-bold uppercase tracking-wide text-slate-400"
          >
            Deadline
          </label>

          <select
            v-model="filters.overdue"
            class="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-2.5 text-sm font-semibold text-slate-700 outline-none transition focus:border-blue-400 focus:bg-white"
          >
            <option value="">All</option>
            <option value="true">Overdue</option>
            <option value="false">Not overdue</option>
          </select>
        </div>
        <div>
          <label
            class="mb-1 block text-xs font-bold uppercase tracking-wide text-slate-400"
          >
            Label
          </label>

          <select
            v-model="filters.label_id"
            class="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-2.5 text-sm font-semibold text-slate-700 outline-none transition focus:border-blue-400 focus:bg-white"
          >
            <option value="">All labels</option>

            <option
              v-for="label in projectLabels"
              :key="label.id"
              :value="label.id"
            >
              {{ label.name }}
            </option>
          </select>
        </div>
      </div>

      <div class="mt-4 flex flex-wrap items-center justify-between gap-3">
        <div class="flex items-center gap-3 text-sm text-slate-500">
          <span v-if="filterLoading" class="font-semibold text-blue-600">
            Filtering...
          </span>

          <span v-else>
            Showing
            <b class="text-slate-900">{{ issues.length }}</b>
            issue(s)
          </span>
        </div>

        <div class="flex items-center gap-2">
          <select
            v-model="filters.order"
            class="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-2 text-sm font-semibold text-slate-700 outline-none transition focus:border-blue-400 focus:bg-white"
          >
            <option value="desc">Newest first</option>
            <option value="asc">Oldest first</option>
          </select>

          <button
            type="button"
            class="rounded-2xl border border-slate-200 px-4 py-2 text-sm font-bold text-slate-600 transition hover:bg-slate-100"
            @click="clearIssueFilters"
          >
            Clear
          </button>
        </div>
      </div>
    </section>

    <div v-if="loading" class="flex gap-4 overflow-x-auto pb-5">
      <div
        v-for="i in 4"
        :key="i"
        class="h-[620px] w-80 shrink-0 animate-pulse rounded-3xl bg-white"
      ></div>
    </div>

    <div v-else class="-mx-5 overflow-x-auto px-5 pb-6">
      <div class="flex min-w-max gap-4">
        <BoardColumn
          v-for="column in columns"
          :key="column.id"
          :column="column"
          :issues="issuesByColumn(column.id)"
          @create-issue="openCreateIssue"
          @open-issue="selectedIssue = $event"
          @drag-issue="onDragIssue"
          @drop-issue="onDropIssue"
        />
      </div>
    </div>

    <div
      v-if="lastEvent"
      class="fixed bottom-5 right-5 z-40 max-w-sm rounded-2xl border border-slate-200 bg-white px-4 py-3 shadow-soft"
    >
      <p class="text-xs font-black uppercase tracking-wide text-slate-400">
        Realtime event
      </p>
      <p class="mt-1 text-sm font-bold text-slate-900">{{ lastEvent.event }}</p>
    </div>

    <section
      class="mb-6 rounded-3xl mt-10 border border-slate-200 bg-white p-5 shadow-sm"
    >
      <div class="mb-4 flex items-center justify-between gap-3">
        <div class="flex items-center gap-3">
          <div
            class="flex h-10 w-10 items-center justify-center rounded-2xl bg-slate-900 text-white"
          >
            <Activity class="h-5 w-5" />
          </div>

          <div>
            <h2 class="text-base font-black text-slate-950">
              Project Activity
            </h2>
            <p class="text-sm text-slate-500">Recent changes in this project</p>
          </div>
        </div>

        <button
          type="button"
          class="rounded-2xl border border-slate-200 px-4 py-2 text-sm font-bold text-slate-600 transition hover:bg-slate-100"
          :disabled="projectLogLoading"
          @click="loadProjectLogs({ reset: true })"
        >
          <RefreshCcw class="mr-2 inline h-4 w-4" />
          Refresh
        </button>
      </div>

      <div
        v-if="projectLogLoading"
        class="rounded-2xl bg-slate-50 p-4 text-sm font-semibold text-slate-500"
      >
        Loading activity logs...
      </div>

      <div
        v-else-if="projectLogs.length === 0"
        class="rounded-2xl bg-slate-50 p-4 text-sm font-semibold text-slate-500"
      >
        No activity yet.
      </div>

      <div
        v-else
        class="max-h-80 space-y-3 overflow-y-auto pr-1"
        @scroll="onProjectLogScroll"
      >
        <div
          v-for="log in projectLogs"
          :key="log.id"
          class="rounded-2xl border border-slate-100 bg-slate-50 p-4"
        >
          <div class="flex flex-wrap items-start justify-between gap-3">
            <div class="min-w-0">
              <div class="mb-2 flex flex-wrap items-center gap-2">
                <span
                  class="rounded-full border px-3 py-1 text-xs font-black"
                  :class="getActivityClass(log.action)"
                >
                  {{ getActivityLabel(log.action) }}
                </span>

                <span class="text-xs font-semibold text-slate-400">
                  {{ formatLogTime(log.created_at) }}
                </span>
              </div>

              <p class="text-sm font-bold text-slate-900">
                {{ log.message }}
              </p>

              <p
                v-if="getChangedFields(log)"
                class="mt-1 text-xs font-semibold text-slate-500"
              >
                Changed:
                <span class="text-slate-700">
                  {{ getChangedFields(log) }}
                </span>
              </p>
            </div>

            <div
              v-if="log.actor"
              class="shrink-0 rounded-2xl bg-white px-3 py-2 text-right shadow-sm"
            >
              <p class="text-xs font-black text-slate-900">
                {{ log.actor.full_name }}
              </p>
            </div>
          </div>
        </div>
        <div
          v-if="projectLogLoadingMore"
          class="rounded-2xl bg-slate-50 p-4 text-center text-sm font-semibold text-slate-500"
        >
          Loading more activity...
        </div>

        <div
          v-else-if="!projectLogHasMore && projectLogs.length > 0"
          class="rounded-2xl bg-slate-50 p-4 text-center text-xs font-bold uppercase tracking-wide text-slate-400"
        >
          No more activity logs
        </div>
      </div>
    </section>

    <IssueFormModal
      v-if="showIssueForm && selectedColumn"
      :project-id="projectId"
      :column="selectedColumn"
      :members="members"
      @close="showIssueForm = false"
      @created="onIssueCreated"
    />

    <IssueDetailModal
      v-if="selectedIssue"
      :can-edit="canEditIssues"
      :project-id="projectId"
      :issue="selectedIssue"
      :members="members"
      :project-labels="projectLabels"
      :epics="epics"
      :sprints="sprints"
      @close="closeIssueModal"
      @changed="onIssueChanged"
      @deleted="onIssueDeleted"
    />

    <AddMemberModal
      v-if="showAddMember"
      :project-id="projectId"
      @close="showAddMember = false"
      @added="onMemberAdded"
    />
  </AppLayout>
</template>
