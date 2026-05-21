<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import {
  ArrowLeft,
  CheckCircle2,
  Columns3,
  Play,
  RefreshCcw,
  Target,
} from "lucide-vue-next";

import IssueCard from "../components/IssueCard.vue";
import IssueDetailModal from "../components/IssueDetailModal.vue";
import { useBoardCore } from "../composables/useBoardCore";
import { useBoardRealtime } from "../composables/useBoardRealtime";
import { useProjectLabels } from "../composables/useProjectLabels";
import { useProjectMembers } from "../composables/useProjectMembers";
import { useProjectPlanning } from "../composables/useProjectPlanning";
import { useSprintIssues } from "../composables/useSprintIssues";
import { formatDateTime } from "../utils/dateUtils";

const route = useRoute();
const router = useRouter();

const projectId = computed(() => Number(route.params.id));
const sprintId = computed(() => Number(route.params.sprintId));

const issues = ref([]);
const error = ref("");

const { refreshIssues } = useSprintIssues({ projectId, sprintId, issues, error });

const {
  project,
  columns,
  loading,
  selectedIssue,
  issueTotal,
  doneTotal,
  issuesByColumn,
  loadBoard,
  onIssueChanged,
  onDragIssue,
  onDropIssue,
  applyIssueMovedLocal,
  openIssueFromQuery,
  closeIssueModal,
} = useBoardCore({
  projectId,
  route,
  router,
  issues,
  error,
  refreshIssues,
});

const {
  members,
  canEditIssues,
  loadCurrentUser,
  loadProjectMembers,
} = useProjectMembers({ projectId, project, error });

const {
  epics,
  sprints,
  loadEpics,
  loadSprints,
  startSprint,
  completeSprint,
} = useProjectPlanning({
  projectId,
  error,
  refreshIssues,
  canEditIssues,
});

const { projectLabels, loadProjectLabels } = useProjectLabels({
  projectId,
  error,
  refreshIssues,
  canManageColumns: canEditIssues,
});

const sprint = computed(() => {
  return sprints.value.find((item) => Number(item.id) === sprintId.value) || null;
});

const progressPercent = computed(() => {
  if (issueTotal.value === 0) return 0;
  return Math.round((doneTotal.value * 100) / issueTotal.value);
});

async function loadPage(options = {}) {
  const silent = options.silent ?? false;

  if (!silent) {
    error.value = "";
  }

  await Promise.all([
    loadCurrentUser(),
    loadBoard({ silent }),
    loadProjectMembers(),
    loadEpics({ silent: true }),
    loadSprints({ silent: true }),
    loadProjectLabels({ silent: true }),
  ]);

  await openIssueFromQuery();
}

function openIssue(issue) {
  selectedIssue.value = issue;
}

const { socketStatus, connectRealtime, closeRealtime } = useBoardRealtime({
  projectId,
  loadEpics,
  loadSprints,
  refreshIssues,
  loadProjectLabels,
  loadProjectMembers,
  loadBoard,
  applyIssueMovedLocal,
});

onMounted(async () => {
  await loadPage();
  connectRealtime();
});

onBeforeUnmount(() => {
  closeRealtime();
});
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

      <section class="mb-6 rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
        <div class="flex flex-wrap items-start justify-between gap-4">
          <div class="min-w-0">
            <div class="mb-3 flex flex-wrap items-center gap-2">
              <span class="rounded-full bg-slate-100 px-3 py-1 text-xs font-black text-slate-500">
                {{ project?.name || "Project" }}
              </span>

              <span
                v-if="sprint"
                class="rounded-full px-3 py-1 text-xs font-black"
                :class="sprint.status === 'ACTIVE'
                  ? 'bg-emerald-50 text-emerald-700'
                  : sprint.status === 'COMPLETED'
                    ? 'bg-slate-200 text-slate-600'
                    : 'bg-blue-50 text-blue-700'"
              >
                {{ sprint.status }}
              </span>

              <span
                class="rounded-full px-3 py-1 text-xs font-black"
                :class="socketStatus === 'connected'
                  ? 'bg-emerald-50 text-emerald-700'
                  : 'bg-slate-100 text-slate-500'"
              >
                {{ socketStatus }}
              </span>
            </div>

            <div class="flex items-center gap-3">
              <div class="flex h-12 w-12 items-center justify-center rounded-2xl bg-slate-900 text-white">
                <Columns3 class="h-6 w-6" />
              </div>

              <div>
                <h1 class="text-2xl font-black text-slate-950">
                  {{ sprint?.name || "Sprint Board" }}
                </h1>

                <p
                  v-if="sprint?.goal"
                  class="mt-1 flex items-start gap-2 text-sm font-medium text-slate-500"
                >
                  <Target class="mt-0.5 h-4 w-4 shrink-0" />
                  {{ sprint.goal }}
                </p>

                <p
                  v-if="sprint?.start_date || sprint?.end_date"
                  class="mt-1 text-xs font-bold text-slate-400"
                >
                  {{ sprint.start_date ? formatDateTime(sprint.start_date) : "No start" }}
                  →
                  {{ sprint.end_date ? formatDateTime(sprint.end_date) : "No end" }}
                </p>
              </div>
            </div>
          </div>

          <div class="flex flex-wrap items-center gap-2">
            <router-link
              :to="`/projects/${projectId}/backlog`"
              class="rounded-2xl border border-slate-200 px-4 py-2 text-sm font-black text-slate-600 transition hover:bg-slate-100"
            >
              Backlog
            </router-link>

            <button
              type="button"
              class="rounded-2xl border border-slate-200 px-4 py-2 text-sm font-black text-slate-600 transition hover:bg-slate-100"
              :disabled="loading"
              @click="loadPage"
            >
              <RefreshCcw class="mr-2 inline h-4 w-4" />
              Refresh
            </button>

            <button
              v-if="canEditIssues && sprint?.status === 'PLANNED'"
              type="button"
              class="rounded-2xl bg-emerald-600 px-4 py-2 text-sm font-black text-white transition hover:bg-emerald-700"
              @click="startSprint(sprint)"
            >
              <Play class="mr-2 inline h-4 w-4" />
              Start
            </button>

            <button
              v-if="canEditIssues && sprint?.status === 'ACTIVE'"
              type="button"
              class="rounded-2xl bg-slate-900 px-4 py-2 text-sm font-black text-white transition hover:bg-slate-800"
              @click="completeSprint(sprint)"
            >
              <CheckCircle2 class="mr-2 inline h-4 w-4" />
              Complete
            </button>
          </div>
        </div>
      </section>

      <section class="mb-6 grid gap-4 md:grid-cols-3">
        <div class="rounded-3xl border border-slate-100 bg-white p-5 shadow-sm">
          <p class="text-sm font-black uppercase tracking-wide text-slate-400">
            Sprint issues
          </p>
          <p class="mt-2 text-3xl font-black text-slate-950">
            {{ issueTotal }}
          </p>
        </div>

        <div class="rounded-3xl border border-emerald-100 bg-emerald-50 p-5 shadow-sm">
          <p class="text-sm font-black uppercase tracking-wide text-emerald-600">
            Done
          </p>
          <p class="mt-2 text-3xl font-black text-emerald-700">
            {{ doneTotal }}
          </p>
        </div>

        <div class="rounded-3xl border border-blue-100 bg-blue-50 p-5 shadow-sm">
          <p class="text-sm font-black uppercase tracking-wide text-blue-600">
            Progress
          </p>

          <p class="mt-2 text-3xl font-black text-blue-700">
            {{ progressPercent }}%
          </p>

          <div class="mt-3 h-2 overflow-hidden rounded-full bg-white">
            <div
              class="h-full rounded-full bg-blue-600"
              :style="{ width: `${progressPercent}%` }"
            ></div>
          </div>
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
        Loading sprint board...
      </div>

      <section
        v-else
        class="flex gap-5 overflow-x-auto pb-4"
      >
        <div
          v-for="column in columns"
          :key="column.id"
          class="min-w-[320px] max-w-[360px] flex-1 rounded-3xl border border-slate-200 bg-white p-4 shadow-sm"
          @dragover.prevent
          @drop.prevent="onDropIssue(column)"
        >
          <div class="mb-4 flex items-center justify-between gap-3">
            <h2 class="font-black text-slate-950">
              {{ column.name }}
            </h2>

            <span class="rounded-full bg-slate-100 px-3 py-1 text-xs font-black text-slate-500">
              {{ issuesByColumn(column.id).length }}
            </span>
          </div>

          <div class="min-h-[460px] rounded-2xl border border-dashed border-transparent p-2 transition hover:border-blue-200 hover:bg-blue-50/40">
            <div
              v-if="issuesByColumn(column.id).length === 0"
              class="rounded-2xl bg-slate-50 p-5 text-center text-sm font-semibold text-slate-400"
            >
              Drop issues here.
            </div>

            <div
              v-else
              class="space-y-3"
            >
              <div
                v-for="issue in issuesByColumn(column.id)"
                :key="issue.id"
                :draggable="canEditIssues"
                class="cursor-grab active:cursor-grabbing"
                @dragstart="onDragIssue(issue)"
              >
                <IssueCard
                  :issue="issue"
                  :members="members"
                  :epics="epics"
                  :sprints="sprints"
                  @click="openIssue(issue)"
                />
              </div>
            </div>
          </div>
        </div>
      </section>

      <IssueDetailModal
        v-if="selectedIssue"
        :project-id="projectId"
        :issue="selectedIssue"
        :members="members"
        :project-labels="projectLabels"
        :epics="epics"
        :sprints="sprints"
        :can-edit="canEditIssues"
        @close="closeIssueModal"
        @changed="onIssueChanged"
      />
    </div>
  </main>
</template>
