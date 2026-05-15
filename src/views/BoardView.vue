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
import AppLayout from "../components/AppLayout.vue";
import AddMemberModal from "../components/AddMemberModal.vue";
import BoardColumn from "../components/BoardColumn.vue";
import IssueDetailModal from "../components/IssueDetailModal.vue";
import IssueFormModal from "../components/IssueFormModal.vue";
import ProjectDashboard from "../components/ProjectDashboard.vue";
import BoardHeader from "../components/board/BoardHeader.vue";
import BoardStats from "../components/board/BoardStats.vue";
import IssueFilters from "../components/board/IssueFilters.vue";
import PlanningPanel from "../components/board/PlanningPanel.vue";
import ProjectActivityPanel from "../components/board/ProjectActivityPanel.vue";
import ProjectLabelsPanel from "../components/board/ProjectLabelsPanel.vue";
import ProjectMembersPanel from "../components/board/ProjectMembersPanel.vue";
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
import { normalizeMember } from "../utils/memberUtils";

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
    const [projectData, columnData, memberData] = await Promise.all([
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
    <BoardHeader
      :project="project"
      :socket-status="socketStatus"
      :avatars="projectMemberAvatars"
      :visible-avatars="visibleProjectMembers"
      :hidden-count="hiddenProjectMemberCount"
      :can-create-issue="canEditIssues"
      :can-add-member="canManageMembers || currentProjectRole === 'ADMIN'"
      :has-columns="columns.length > 0"
      @back="router.push('/projects')"
      @refresh="loadBoard"
      @add-member="showAddMember = true"
      @dashboard="router.push(`/projects/${projectId}/dashboard`)"
      @create-issue="openCreateIssue(columns[0])"
    />

    <BoardStats
      :issue-total="issueTotal"
      :done-total="doneTotal"
      :members-count="members.length"
    />

    <p
      v-if="error"
      class="mb-4 rounded-xl bg-rose-50 px-4 py-3 text-sm font-medium text-rose-700"
    >
      {{ error }}
    </p>

    <ProjectMembersPanel
      :members="projectMemberAvatars"
      :project="project"
      :current-role="currentProjectRole"
      :can-manage="canManageMembers"
      @update-role="updateMemberRole"
      @remove-member="removeProjectMember"
    />

    <ProjectLabelsPanel
      :labels="projectLabels"
      :loading="labelLoading"
      :form="labelForm"
      :can-edit="canManageColumns"
      @create="createProjectLabel"
      @delete="deleteProjectLabel"
    />

    <ProjectDashboard :project-id="projectId" />

    <PlanningPanel
      :epics="epics"
      :sprints="sprints"
      :epic-form="epicForm"
      :sprint-form="sprintForm"
      :epic-loading="epicLoading"
      :sprint-loading="sprintLoading"
      :can-edit="canEditIssues"
      @create-epic="createEpic"
      @delete-epic="deleteEpic"
      @create-sprint="createSprint"
      @delete-sprint="deleteSprint"
    />

    <IssueFilters
      :filters="filters"
      :columns="columns"
      :labels="projectLabels"
      :issues-count="issues.length"
      :loading="filterLoading"
      @clear="clearIssueFilters"
    />

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
          :members="members"
          :epics="epics"
          :sprints="sprints"
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

    <ProjectActivityPanel
      :logs="projectLogs"
      :loading="projectLogLoading"
      :loading-more="projectLogLoadingMore"
      :has-more="projectLogHasMore"
      @refresh="loadProjectLogs({ reset: true })"
      @scroll="onProjectLogScroll"
    />

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
