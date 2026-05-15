<script setup>
import { computed, onBeforeUnmount, onMounted, watch, ref } from "vue";
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

import { useBoardCore } from "../composables/useBoardCore";
import { useBoardRealtime } from "../composables/useBoardRealtime";
import { useIssueFilters } from "../composables/useIssueFilters";
import { useProjectActivity } from "../composables/useProjectActivity";
import { useProjectLabels } from "../composables/useProjectLabels";
import { useProjectMembers } from "../composables/useProjectMembers";
import { useProjectPlanning } from "../composables/useProjectPlanning";

const route = useRoute();
const router = useRouter();
const projectId = computed(() => Number(route.params.id));

const issues = ref([]);
const error = ref("");

const {
  filters,
  filterLoading,
  refreshIssues,
  clearIssueFilters,
  cleanupIssueFilters,
} = useIssueFilters({ projectId, issues, error });

const {
  project,
  columns,
  loading,
  showIssueForm,
  selectedColumn,
  selectedIssue,
  issueTotal,
  doneTotal,
  issuesByColumn,
  loadBoard,
  openCreateIssue,
  onIssueCreated,
  onIssueChanged,
  onIssueDeleted,
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
  showAddMember,
  projectMemberAvatars,
  visibleProjectMembers,
  hiddenProjectMemberCount,
  currentProjectRole,
  canManageMembers,
  canManageColumns,
  canEditIssues,
  loadCurrentUser,
  loadProjectMembers,
  updateMemberRole,
  removeProjectMember,
  onMemberAdded,
} = useProjectMembers({ projectId, project, error });

const {
  projectLabels,
  labelLoading,
  labelForm,
  loadProjectLabels,
  createProjectLabel,
  deleteProjectLabel,
} = useProjectLabels({
  projectId,
  error,
  refreshIssues,
  canManageColumns,
});

const {
  epics,
  sprints,
  epicLoading,
  sprintLoading,
  epicForm,
  sprintForm,
  loadEpics,
  loadSprints,
  createEpic,
  createSprint,
  deleteEpic,
  deleteSprint,
} = useProjectPlanning({
  projectId,
  error,
  refreshIssues,
  canEditIssues,
});

const {
  projectLogs,
  projectLogLoading,
  projectLogLoadingMore,
  projectLogHasMore,
  loadProjectLogs,
  onProjectLogScroll,
} = useProjectActivity({ projectId, error });

const { socketStatus, lastEvent, connectRealtime, closeRealtime } =
  useBoardRealtime({
    projectId,
    loadEpics,
    loadSprints,
    refreshIssues,
    loadProjectLabels,
    loadProjectLogs,
    loadProjectMembers,
    loadBoard,
    applyIssueMovedLocal,
  });

onMounted(async () => {
  await Promise.all([
    loadCurrentUser(),
    loadBoard(),
    loadProjectMembers(),
    loadProjectLabels({ silent: true }),
    loadEpics({ silent: true }),
    loadSprints({ silent: true }),
    loadProjectLogs({ reset: true, silent: true }),
  ]);

  await openIssueFromQuery();
  connectRealtime();
});

watch(
  () => route.query.issueId,
  () => {
    openIssueFromQuery();
  },
);

onBeforeUnmount(() => {
  cleanupIssueFilters();
  closeRealtime();
});
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
