<script setup>
import { onBeforeUnmount, onMounted, ref } from "vue";
import { Activity, Clock3, RefreshCcw } from "lucide-vue-next";
import { activityApi, getErrorMessage } from "../../services/api";
import { getInitials } from "../../utils/memberUtils";
import { getActivityLabel, getActivityClass, getChangedFields } from "../../utils/activityUtils";
const props = defineProps({
  issue: { type: Object, required: true },
});

const logs = ref([]);
const loading = ref(false);
const loadingMore = ref(false);
const hasMore = ref(true);
const error = ref("");

const LIMIT = 10;

async function loadActivities(options = {}) {
  const reset = options.reset ?? false;
  const silent = options.silent ?? false;

  if (loading.value || loadingMore.value) return;
  if (!reset && !hasMore.value) return;

  const offset = reset ? 0 : logs.value.length;

  if (reset) {
    hasMore.value = true;
    if (!silent) loading.value = true;
  } else {
    loadingMore.value = true;
  }

  error.value = "";

  try {
    const data = await activityApi.listIssueLog(props.issue.id, {
      limit: LIMIT,
      offset,
    });

    if (reset) {
      logs.value = data;
    } else {
      const currentIds = new Set(logs.value.map((item) => item.id));
      logs.value = [...logs.value, ...data.filter((item) => !currentIds.has(item.id))];
    }

    hasMore.value = data.length === LIMIT;
  } catch (err) {
    error.value = getErrorMessage(err);
  } finally {
    loading.value = false;
    loadingMore.value = false;
  }
}

function onScroll(event) {
  const el = event.target;
  const nearBottom = el.scrollTop + el.clientHeight >= el.scrollHeight - 80;

  if (nearBottom) {
    loadActivities({ reset: false, silent: true });
  }
}

function onRealtime(event) {
  const issueId = Number(event.detail?.issue_id);

  if (!issueId || issueId === Number(props.issue.id)) {
    loadActivities({ reset: true, silent: true });
  }
}

function formatTime(value) {
  if (!value) return "";
  return new Date(value).toLocaleString();
}

onMounted(() => {
  loadActivities({ reset: true, silent: true });
  window.addEventListener("jira-activity-refresh", onRealtime);
  window.addEventListener("jira-epic-sprint-refresh", onRealtime);
});

onBeforeUnmount(() => {
  window.removeEventListener("jira-activity-refresh", onRealtime);
  window.removeEventListener("jira-epic-sprint-refresh", onRealtime);
});
</script>

<template>
  <section class="rounded-2xl border border-slate-200 bg-slate-50 p-4">
    <div class="mb-4 flex items-center justify-between gap-3">
      <div class="flex items-center gap-2">
        <Activity class="h-5 w-5 text-slate-500" />
        <h3 class="font-black text-slate-950">Activity</h3>
      </div>

      <button
        type="button"
        class="rounded-xl border border-slate-200 bg-white px-3 py-2 text-xs font-black text-slate-600 transition hover:bg-slate-100"
        :disabled="loading"
        @click="loadActivities({ reset: true })"
      >
        <RefreshCcw class="mr-1 inline h-3.5 w-3.5" />
        Refresh
      </button>
    </div>

    <p v-if="error" class="mb-3 rounded-xl bg-rose-50 px-4 py-3 text-sm font-medium text-rose-700">
      {{ error }}
    </p>

    <div v-if="loading" class="rounded-2xl bg-white p-4 text-sm text-slate-500">
      Loading activity...
    </div>

    <div v-else-if="logs.length === 0" class="rounded-2xl bg-white p-4 text-sm text-slate-500">
      No activity yet.
    </div>

    <div v-else class="max-h-96 space-y-3 overflow-y-auto pr-1" @scroll="onScroll">
      <div v-for="log in logs" :key="log.id" class="rounded-2xl bg-white p-4 shadow-sm">
        <div class="flex items-start gap-3">
          <div class="mt-1 flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-slate-900 text-white">
            <Clock3 class="h-4 w-4" />
          </div>

          <div class="min-w-0 flex-1">
            <div class="mb-2 flex flex-wrap items-center gap-2">
              <span class="rounded-full border px-3 py-1 text-xs font-black" :class="getActivityClass(log.action)">
                {{ getActivityLabel(log.action) }}
              </span>

              <span class="text-xs font-semibold text-slate-400">
                {{ formatTime(log.created_at) }}
              </span>
            </div>

            <p class="text-sm font-bold text-slate-900">{{ log.message }}</p>

            <p v-if="getChangedFields(log)" class="mt-1 text-xs font-semibold text-slate-500">
              Changed:
              <span class="text-slate-700">{{ getChangedFields(log) }}</span>
            </p>

            <div v-if="log.actor" class="mt-2 inline-flex items-center gap-2 rounded-full bg-slate-50 px-3 py-1.5">
              <div class="flex h-6 w-6 items-center justify-center rounded-full bg-slate-800 text-[10px] font-black text-white">
                {{ getInitials(log.actor.full_name) }}
              </div>

              <span class="text-xs font-bold text-slate-600">{{ log.actor.full_name }}</span>
            </div>
          </div>
        </div>
      </div>

      <div v-if="loadingMore" class="rounded-2xl bg-white p-4 text-center text-sm font-semibold text-slate-500">
        Loading more activity...
      </div>

      <div
        v-else-if="!hasMore && logs.length > 0"
        class="rounded-2xl bg-white p-4 text-center text-xs font-bold uppercase tracking-wide text-slate-400"
      >
        No more activity
      </div>
    </div>
  </section>
</template>
