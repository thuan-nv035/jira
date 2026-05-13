<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import {
  ArrowLeft,
  Plus,
  RefreshCcw,
  UserPlus,
  Wifi,
  WifiOff,
} from "lucide-vue-next";
import AppLayout from "../components/AppLayout.vue";
import AddMemberModal from "../components/AddMemberModal.vue";
import BoardColumn from "../components/BoardColumn.vue";
import IssueDetailModal from "../components/IssueDetailModal.vue";
import IssueFormModal from "../components/IssueFormModal.vue";
import {
  columnApi,
  getErrorMessage,
  issueApi,
  projectApi,
} from "../services/api";
import { createProjectSocket } from "../services/socket";

const route = useRoute();
const router = useRouter();
const projectId = computed(() => Number(route.params.id));

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

async function loadBoard() {
  loading.value = true;
  error.value = "";
  try {
    const [projectData, columnData, issueData, memberData] = await Promise.all([
      projectApi.get(projectId.value),
      columnApi.list(projectId.value),
      issueApi.list(projectId.value),
      projectApi.members(projectId.value),
    ]);
    project.value = projectData;
    columns.value = columnData;
    issues.value = issueData;
    members.value = memberData;
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
  if (payload.event === "notification.created") {
    window.dispatchEvent(
      new CustomEvent("jira-notification-refresh", { detail: payload.data }),
    );
  }

  if (
    [
      "issue.created",
      "issue.updated",
      "issue.moved",
      "issue.deleted",
      "comment.created",
      "column.created",
      "column.updated",
      "column.deleted",
      "member.added",
      "notification.created",
      "attachment.uploaded",
      "attachment.deleted",
    ].includes(payload.event)
  ) {
    loadBoard();
  }

  if (["attachment.uploaded", "attachment.deleted"].includes(payload.event)) {
    window.dispatchEvent(
      new CustomEvent("jira-attachment-refresh", { detail: payload.data }),
    );
  }
}

function onMemberAdded(member) {
  showAddMember.value = false;
  members.value = [...members.value, member];
}

onMounted(async () => {
  await loadBoard();
  socket = createProjectSocket(projectId.value, onSocketMessage, (status) => {
    socketStatus.value = status;
  });
});

onBeforeUnmount(() => {
  socket?.close();
});
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
      :project-id="projectId"
      :issue="selectedIssue"
      :members="members"
      @close="selectedIssue = null"
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
