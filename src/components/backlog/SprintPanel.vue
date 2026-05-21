<script setup>
import { computed } from "vue";
import { CheckCircle2, Play, RefreshCcw, Target } from "lucide-vue-next";
import BacklogIssueItem from "./BacklogIssueItem.vue";
import { formatDateTime } from "../../utils/dateUtils";

const props = defineProps({
  sprint: {
    type: Object,
    required: true,
  },
  issues: {
    type: Array,
    default: () => [],
  },
  allSprints: {
    type: Array,
    default: () => [],
  },
  loading: {
    type: Boolean,
    default: false,
  },
  canEdit: {
    type: Boolean,
    default: true,
  },
});

const emit = defineEmits([
  "refresh",
  "open-issue",
  "move-to-sprint",
  "move-to-backlog",
  "start",
  "complete",
  "drop-issue",
  "drag-start",
  "drag-end",
]);

const statusClass = computed(() => {
  if (props.sprint.status === "ACTIVE") {
    return "bg-emerald-50 text-emerald-700";
  }

  if (props.sprint.status === "COMPLETED") {
    return "bg-slate-200 text-slate-600";
  }

  return "bg-blue-50 text-blue-700";
});
</script>

<template>
  <section class="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
    <div class="mb-4 flex flex-wrap items-start justify-between gap-4">
      <div class="min-w-0">
        <div class="mb-2 flex flex-wrap items-center gap-2">
          <span
            class="rounded-full px-3 py-1 text-xs font-black"
            :class="statusClass"
          >
            {{ sprint.status }}
          </span>

          <span
            class="rounded-full bg-slate-100 px-3 py-1 text-xs font-black text-slate-500"
          >
            {{ issues.length }} issue(s)
          </span>
        </div>

        <h2 class="text-lg font-black text-slate-950">
          {{ sprint.name }}
        </h2>

        <p
          v-if="sprint.goal"
          class="mt-1 flex items-start gap-2 text-sm font-medium text-slate-500"
        >
          <Target class="mt-0.5 h-4 w-4 shrink-0" />
          {{ sprint.goal }}
        </p>

        <p
          v-if="sprint.start_date || sprint.end_date"
          class="mt-2 text-xs font-bold text-slate-400"
        >
          {{
            sprint.start_date ? formatDateTime(sprint.start_date) : "No start"
          }}
          →
          {{ sprint.end_date ? formatDateTime(sprint.end_date) : "No end" }}
        </p>
      </div>

      <div class="flex flex-wrap gap-2">
        <router-link
          :to="`/projects/${sprint.project_id}/sprints/${sprint.id}`"
          class="rounded-2xl border border-blue-200 px-3 py-2 text-xs font-black text-blue-600 transition hover:bg-blue-50"
        >
          Open board
        </router-link>
        <button
          type="button"
          class="rounded-2xl border border-slate-200 px-3 py-2 text-xs font-black text-slate-600 transition hover:bg-slate-100"
          :disabled="loading"
          @click="emit('refresh', sprint)"
        >
          <RefreshCcw class="mr-1 inline h-3.5 w-3.5" />
          Refresh
        </button>

        <button
          v-if="canEdit && sprint.status === 'PLANNED'"
          type="button"
          class="rounded-2xl bg-emerald-600 px-3 py-2 text-xs font-black text-white transition hover:bg-emerald-700"
          @click="emit('start', sprint)"
        >
          <Play class="mr-1 inline h-3.5 w-3.5" />
          Start
        </button>

        <button
          v-if="canEdit && sprint.status === 'ACTIVE'"
          type="button"
          class="rounded-2xl bg-slate-900 px-3 py-2 text-xs font-black text-white transition hover:bg-slate-800"
          @click="emit('complete', sprint)"
        >
          <CheckCircle2 class="mr-1 inline h-3.5 w-3.5" />
          Complete
        </button>
      </div>
    </div>

    <div
      v-if="loading"
      class="rounded-2xl bg-slate-50 p-4 text-sm font-semibold text-slate-500"
    >
      Loading sprint issues...
    </div>

    <div
      v-else-if="issues.length === 0"
      class="rounded-2xl bg-slate-50 p-5 text-center text-sm font-semibold text-slate-400"
    >
      No issues in this sprint.
    </div>

    <div
      class="min-h-[120px] rounded-3xl border border-dashed border-transparent transition"
      @dragover.prevent
      @drop.prevent="emit('drop-issue', sprint)"
    >
      <div
        v-if="loading"
        class="rounded-2xl bg-slate-50 p-4 text-sm font-semibold text-slate-500"
      >
        Loading sprint issues...
      </div>

      <div
        v-else-if="issues.length === 0"
        class="rounded-2xl border border-dashed border-blue-200 bg-blue-50/60 p-5 text-center text-sm font-semibold text-blue-500"
      >
        Drop issues here to add them to this sprint.
      </div>

      <div v-else class="space-y-3">
        <BacklogIssueItem
          v-for="issue in issues"
          :key="issue.id"
          :issue="issue"
          :sprints="allSprints"
          :can-edit="canEdit"
          mode="sprint"
          @open="emit('open-issue', $event)"
          @move-to-sprint="emit('move-to-sprint', $event)"
          @move-to-backlog="emit('move-to-backlog', $event)"
          @drag-start="emit('drag-start', $event)"
          @drag-end="emit('drag-end')"
        />
      </div>
    </div>
  </section>
</template>
