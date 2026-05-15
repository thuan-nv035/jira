<script setup>
import { Activity, RefreshCcw } from "lucide-vue-next";
import { getActivityLabel, getActivityClass, getChangedFields } from "../../utils/activityUtils";

defineProps({
  logs: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
  loadingMore: { type: Boolean, default: false },
  hasMore: { type: Boolean, default: true },
});

const emit = defineEmits(["refresh", "scroll"]);

function formatTime(value) {
  if (!value) return "";
  return new Date(value).toLocaleString();
}
</script>

<template>
  <section class="mb-6 mt-10 rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
    <div class="mb-4 flex items-center justify-between gap-3">
      <div class="flex items-center gap-3">
        <div class="flex h-10 w-10 items-center justify-center rounded-2xl bg-slate-900 text-white">
          <Activity class="h-5 w-5" />
        </div>

        <div>
          <h2 class="text-base font-black text-slate-950">Project Activity</h2>
          <p class="text-sm text-slate-500">Recent changes in this project</p>
        </div>
      </div>

      <button
        type="button"
        class="rounded-2xl border border-slate-200 px-4 py-2 text-sm font-bold text-slate-600 transition hover:bg-slate-100"
        :disabled="loading"
        @click="emit('refresh')"
      >
        <RefreshCcw class="mr-2 inline h-4 w-4" />
        Refresh
      </button>
    </div>

    <div v-if="loading" class="rounded-2xl bg-slate-50 p-4 text-sm font-semibold text-slate-500">
      Loading activity logs...
    </div>

    <div v-else-if="logs.length === 0" class="rounded-2xl bg-slate-50 p-4 text-sm font-semibold text-slate-500">
      No activity yet.
    </div>

    <div
      v-else
      class="max-h-80 space-y-3 overflow-y-auto pr-1"
      @scroll="emit('scroll', $event)"
    >
      <div
        v-for="log in logs"
        :key="log.id"
        class="rounded-2xl border border-slate-100 bg-slate-50 p-4"
      >
        <div class="flex flex-wrap items-start justify-between gap-3">
          <div class="min-w-0">
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
          </div>

          <div v-if="log.actor" class="shrink-0 rounded-2xl bg-white px-3 py-2 text-right shadow-sm">
            <p class="text-xs font-black text-slate-900">{{ log.actor.full_name }}</p>
          </div>
        </div>
      </div>

      <div v-if="loadingMore" class="rounded-2xl bg-slate-50 p-4 text-center text-sm font-semibold text-slate-500">
        Loading more activity...
      </div>

      <div
        v-else-if="!hasMore && logs.length > 0"
        class="rounded-2xl bg-slate-50 p-4 text-center text-xs font-bold uppercase tracking-wide text-slate-400"
      >
        No more activity logs
      </div>
    </div>
  </section>
</template>
