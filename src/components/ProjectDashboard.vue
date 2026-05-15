<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from "vue";
import {
  AlertTriangle,
  BarChart3,
  CheckCircle2,
  Clock3,
  ListTodo,
  RefreshCcw,
  UserRound,
  UsersRound
} from "lucide-vue-next";
import { dashboardApi, getErrorMessage } from "../services/api";
import { getInitials } from "../utils/memberUtils";

const props = defineProps({
  projectId: {
    type: [String, Number],
    required: true
  }
});

const loading = ref(false);
const error = ref("");

const summary = ref({
  total_issues: 0,
  done_issues: 0,
  in_progress_issues: 0,
  overdue_issues: 0,
  unassigned_issues: 0,
  total_members: 0
});

const statusItems = ref([]);
const priorityItems = ref([]);
const assigneeItems = ref([]);
const recentActivity = ref([]);

const maxStatusTotal = computed(() => {
  return Math.max(...statusItems.value.map((item) => item.total), 1);
});

const maxPriorityTotal = computed(() => {
  return Math.max(...priorityItems.value.map((item) => item.total), 1);
});

const maxAssigneeTotal = computed(() => {
  return Math.max(...assigneeItems.value.map((item) => item.total), 1);
});

const donePercent = computed(() => {
  const total = Number(summary.value.total_issues || 0);
  const done = Number(summary.value.done_issues || 0);

  if (total === 0) return 0;

  return Math.round((done * 100) / total);
});

async function loadDashboard(options = {}) {
  const silent = options.silent ?? false;

  if (!props.projectId) return;

  if (!silent) {
    loading.value = true;
  }

  error.value = "";

  try {
    const [
      summaryData,
      statusData,
      priorityData,
      assigneeData,
      activityData
    ] = await Promise.all([
      dashboardApi.summary(props.projectId),
      dashboardApi.issuesByStatus(props.projectId),
      dashboardApi.issuesByPriority(props.projectId),
      dashboardApi.issuesByAssignee(props.projectId),
      dashboardApi.recentActivity(props.projectId, 8)
    ]);

    summary.value = summaryData;
    statusItems.value = statusData;
    priorityItems.value = priorityData;
    assigneeItems.value = assigneeData;
    recentActivity.value = activityData;
  } catch (err) {
    error.value = getErrorMessage(err);
  } finally {
    loading.value = false;
  }
}

function getPriorityClass(priority) {
  const value = String(priority || "").toUpperCase();

  if (value === "URGENT") return "bg-rose-500";
  if (value === "HIGH") return "bg-orange-500";
  if (value === "MEDIUM") return "bg-blue-500";
  if (value === "LOW") return "bg-emerald-500";

  return "bg-slate-500";
}

function getStatusBarClass(index) {
  const colors = [
    "bg-slate-900",
    "bg-blue-600",
    "bg-violet-600",
    "bg-emerald-600",
    "bg-amber-500",
    "bg-rose-500"
  ];

  return colors[index % colors.length];
}

function getAssigneeName(item) {
  if (!item.assignee_id) return "Unassigned";
  return item.full_name || item.email || "Unknown user";
}

function onDashboardRefresh() {
  loadDashboard({ silent: true });
}

onMounted(() => {
  loadDashboard();
  window.addEventListener("jira-dashboard-refresh", onDashboardRefresh);
});

onBeforeUnmount(() => {
  window.removeEventListener("jira-dashboard-refresh", onDashboardRefresh);
});
</script>

<template>
  <section class="mb-6 rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
    <div class="mb-5 flex flex-wrap items-center justify-between gap-3">
      <div>
        <div class="flex items-center gap-3">
          <div class="flex h-11 w-11 items-center justify-center rounded-2xl bg-slate-900 text-white">
            <BarChart3 class="h-5 w-5" />
          </div>

          <div>
            <h2 class="text-lg font-black text-slate-950">
              Project Dashboard
            </h2>
            <p class="text-sm font-medium text-slate-500">
              Overview of issues, progress, members and recent activity
            </p>
          </div>
        </div>
      </div>

      <button
        type="button"
        class="rounded-2xl border border-slate-200 px-4 py-2 text-sm font-bold text-slate-600 transition hover:bg-slate-100 disabled:opacity-60"
        :disabled="loading"
        @click="loadDashboard()"
      >
        <RefreshCcw class="mr-2 inline h-4 w-4" />
        Refresh
      </button>
    </div>

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
      Loading dashboard...
    </div>

    <template v-else>
      <div class="mb-5 grid gap-4 sm:grid-cols-2 xl:grid-cols-6">
        <div class="rounded-3xl border border-slate-100 bg-slate-50 p-4">
          <div class="mb-3 flex items-center justify-between">
            <ListTodo class="h-5 w-5 text-slate-500" />
            <span class="text-xs font-black uppercase tracking-wide text-slate-400">
              Total
            </span>
          </div>
          <p class="text-3xl font-black text-slate-950">
            {{ summary.total_issues }}
          </p>
          <p class="mt-1 text-sm font-semibold text-slate-500">
            Issues
          </p>
        </div>

        <div class="rounded-3xl border border-emerald-100 bg-emerald-50 p-4">
          <div class="mb-3 flex items-center justify-between">
            <CheckCircle2 class="h-5 w-5 text-emerald-600" />
            <span class="text-xs font-black uppercase tracking-wide text-emerald-600">
              Done
            </span>
          </div>
          <p class="text-3xl font-black text-emerald-700">
            {{ summary.done_issues }}
          </p>
          <p class="mt-1 text-sm font-semibold text-emerald-700">
            {{ donePercent }}% completed
          </p>
        </div>

        <div class="rounded-3xl border border-blue-100 bg-blue-50 p-4">
          <div class="mb-3 flex items-center justify-between">
            <Clock3 class="h-5 w-5 text-blue-600" />
            <span class="text-xs font-black uppercase tracking-wide text-blue-600">
              Active
            </span>
          </div>
          <p class="text-3xl font-black text-blue-700">
            {{ summary.in_progress_issues }}
          </p>
          <p class="mt-1 text-sm font-semibold text-blue-700">
            In progress
          </p>
        </div>

        <div class="rounded-3xl border border-rose-100 bg-rose-50 p-4">
          <div class="mb-3 flex items-center justify-between">
            <AlertTriangle class="h-5 w-5 text-rose-600" />
            <span class="text-xs font-black uppercase tracking-wide text-rose-600">
              Overdue
            </span>
          </div>
          <p class="text-3xl font-black text-rose-700">
            {{ summary.overdue_issues }}
          </p>
          <p class="mt-1 text-sm font-semibold text-rose-700">
            Need attention
          </p>
        </div>

        <div class="rounded-3xl border border-amber-100 bg-amber-50 p-4">
          <div class="mb-3 flex items-center justify-between">
            <UserRound class="h-5 w-5 text-amber-600" />
            <span class="text-xs font-black uppercase tracking-wide text-amber-600">
              Unassigned
            </span>
          </div>
          <p class="text-3xl font-black text-amber-700">
            {{ summary.unassigned_issues }}
          </p>
          <p class="mt-1 text-sm font-semibold text-amber-700">
            No assignee
          </p>
        </div>

        <div class="rounded-3xl border border-violet-100 bg-violet-50 p-4">
          <div class="mb-3 flex items-center justify-between">
            <UsersRound class="h-5 w-5 text-violet-600" />
            <span class="text-xs font-black uppercase tracking-wide text-violet-600">
              Members
            </span>
          </div>
          <p class="text-3xl font-black text-violet-700">
            {{ summary.total_members }}
          </p>
          <p class="mt-1 text-sm font-semibold text-violet-700">
            People
          </p>
        </div>
      </div>

      <div class="grid gap-5 xl:grid-cols-3">
        <div class="rounded-3xl border border-slate-100 bg-slate-50 p-4">
          <h3 class="mb-4 text-sm font-black uppercase tracking-wide text-slate-500">
            Issues by status
          </h3>

          <div class="space-y-4">
            <div
              v-for="(item, index) in statusItems"
              :key="item.column_id"
            >
              <div class="mb-1 flex items-center justify-between gap-3 text-sm">
                <span class="truncate font-bold text-slate-700">
                  {{ item.column_name }}
                </span>
                <span class="font-black text-slate-900">
                  {{ item.total }}
                </span>
              </div>

              <div class="h-2 overflow-hidden rounded-full bg-white">
                <div
                  class="h-full rounded-full transition-all duration-300"
                  :class="getStatusBarClass(index)"
                  :style="{ width: `${(item.total / maxStatusTotal) * 100}%` }"
                ></div>
              </div>
            </div>

            <p
              v-if="statusItems.length === 0"
              class="text-sm font-semibold text-slate-400"
            >
              No status data.
            </p>
          </div>
        </div>

        <div class="rounded-3xl border border-slate-100 bg-slate-50 p-4">
          <h3 class="mb-4 text-sm font-black uppercase tracking-wide text-slate-500">
            Issues by priority
          </h3>

          <div class="space-y-4">
            <div
              v-for="item in priorityItems"
              :key="item.priority"
            >
              <div class="mb-1 flex items-center justify-between gap-3 text-sm">
                <div class="flex items-center gap-2">
                  <span
                    class="h-2.5 w-2.5 rounded-full"
                    :class="getPriorityClass(item.priority)"
                  ></span>
                  <span class="font-bold text-slate-700">
                    {{ item.priority }}
                  </span>
                </div>

                <span class="font-black text-slate-900">
                  {{ item.total }}
                </span>
              </div>

              <div class="h-2 overflow-hidden rounded-full bg-white">
                <div
                  class="h-full rounded-full transition-all duration-300"
                  :class="getPriorityClass(item.priority)"
                  :style="{ width: `${(item.total / maxPriorityTotal) * 100}%` }"
                ></div>
              </div>
            </div>

            <p
              v-if="priorityItems.length === 0"
              class="text-sm font-semibold text-slate-400"
            >
              No priority data.
            </p>
          </div>
        </div>

        <div class="rounded-3xl border border-slate-100 bg-slate-50 p-4">
          <h3 class="mb-4 text-sm font-black uppercase tracking-wide text-slate-500">
            Issues by assignee
          </h3>

          <div class="space-y-4">
            <div
              v-for="item in assigneeItems"
              :key="item.assignee_id || 'unassigned'"
            >
              <div class="mb-1 flex items-center justify-between gap-3 text-sm">
                <div class="flex min-w-0 items-center gap-2">
                  <div class="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-slate-900 text-[11px] font-black text-white">
                    {{ getInitials(getAssigneeName(item)) }}
                  </div>

                  <span class="truncate font-bold text-slate-700">
                    {{ getAssigneeName(item) }}
                  </span>
                </div>

                <span class="font-black text-slate-900">
                  {{ item.total }}
                </span>
              </div>

              <div class="h-2 overflow-hidden rounded-full bg-white">
                <div
                  class="h-full rounded-full bg-slate-900 transition-all duration-300"
                  :style="{ width: `${(item.total / maxAssigneeTotal) * 100}%` }"
                ></div>
              </div>
            </div>

            <p
              v-if="assigneeItems.length === 0"
              class="text-sm font-semibold text-slate-400"
            >
              No assignee data.
            </p>
          </div>
        </div>
      </div>

      <!-- <div class="mt-5 rounded-3xl border border-slate-100 bg-slate-50 p-4">
        <h3 class="mb-4 text-sm font-black uppercase tracking-wide text-slate-500">
          Recent activity
        </h3>

        <div class="space-y-3">
          <div
            v-for="log in recentActivity"
            :key="log.id"
            class="rounded-2xl bg-white p-4 shadow-sm"
          >
            <div class="flex flex-wrap items-start justify-between gap-3">
              <div class="min-w-0">
                <p class="text-sm font-bold text-slate-900">
                  {{ log.message }}
                </p>

                <p class="mt-1 text-xs font-semibold text-slate-400">
                  {{ log.action }} · {{ formatActivityTime(log.created_at) }}
                </p>
              </div>

              <div
                v-if="log.actor"
                class="rounded-2xl bg-slate-50 px-3 py-2 text-right"
              >
                <p class="text-xs font-black text-slate-900">
                  {{ log.actor.full_name }}
                </p>
                <p class="text-[11px] text-slate-400">
                  {{ log.actor.email }}
                </p>
              </div>
            </div>
          </div>

          <p
            v-if="recentActivity.length === 0"
            class="rounded-2xl bg-white p-4 text-sm font-semibold text-slate-400"
          >
            No recent activity.
          </p>
        </div>
      </div> -->
    </template>
  </section>
</template>