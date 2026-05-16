<script setup>
import {
  AlertTriangle,
  CalendarDays,
  CheckSquare,
  ExternalLink,
  ListChecks,
  Tag,
} from "lucide-vue-next";
import { formatDateTime } from "../../utils/dateUtils";

const props = defineProps({
  issue: {
    type: Object,
    required: true,
  },
  sprints: {
    type: Array,
    default: () => [],
  },
  canEdit: {
    type: Boolean,
    default: true,
  },
  mode: {
    type: String,
    default: "backlog",
  },
});

const emit = defineEmits([
  "open",
  "move-to-sprint",
  "move-to-backlog",
  "drag-start",
  "drag-end",
]);

function handleDragStart(event) {
  if (!props.canEdit) return;

  event.dataTransfer.effectAllowed = "move";
  event.dataTransfer.setData("text/plain", String(props.issue.id));

  emit("drag-start", props.issue);
}

function handleDragEnd() {
  emit("drag-end");
}

function getPriorityClass(priority) {
  const value = String(priority || "").toUpperCase();

  if (value === "URGENT") return "bg-rose-50 text-rose-700 border-rose-100";
  if (value === "HIGH") return "bg-orange-50 text-orange-700 border-orange-100";
  if (value === "MEDIUM") return "bg-blue-50 text-blue-700 border-blue-100";
  if (value === "LOW")
    return "bg-emerald-50 text-emerald-700 border-emerald-100";

  return "bg-slate-50 text-slate-700 border-slate-100";
}

function checklistPercent(issue) {
  const total = Number(issue.checklist_total || 0);
  const done = Number(issue.checklist_done || 0);

  if (total === 0) return 0;

  return Math.round((done * 100) / total);
}

function onSprintChange(event) {
  const value = event.target.value;

  if (!value) return;

  emit("move-to-sprint", {
    issue: props.issue,
    sprintId: Number(value),
  });

  event.target.value = "";
}
</script>

<template>
  <article
    class="cursor-grab rounded-3xl border border-slate-100 bg-white p-4 shadow-sm transition hover:border-blue-200 hover:shadow-md active:cursor-grabbing"
    :draggable="canEdit"
    @dragstart="handleDragStart"
    @dragend="handleDragEnd"
  >
    <div class="flex flex-wrap items-start justify-between gap-4">
      <button
        type="button"
        class="min-w-0 flex-1 text-left"
        @click="emit('open', issue)"
      >
        <div class="mb-2 flex flex-wrap items-center gap-2">
          <span
            class="rounded-full bg-slate-100 px-3 py-1 text-xs font-black text-slate-600"
          >
            {{ issue.code }}
          </span>

          <span
            class="rounded-full border px-3 py-1 text-xs font-black"
            :class="getPriorityClass(issue.priority)"
          >
            {{ issue.priority }}
          </span>

          <span
            class="rounded-full bg-slate-50 px-3 py-1 text-xs font-black text-slate-500"
          >
            {{ issue.issue_type }}
          </span>

          <span
            v-if="issue.is_overdue"
            class="inline-flex items-center gap-1 rounded-full bg-rose-50 px-3 py-1 text-xs font-black text-rose-700"
          >
            <AlertTriangle class="h-3.5 w-3.5" />
            Overdue
          </span>
        </div>

        <h3 class="line-clamp-2 text-sm font-black text-slate-950">
          {{ issue.title }}
        </h3>

        <p
          v-if="issue.description"
          class="mt-1 line-clamp-2 text-sm font-medium text-slate-500"
        >
          {{ issue.description }}
        </p>

        <div
          v-if="issue.labels && issue.labels.length > 0"
          class="mt-3 flex flex-wrap gap-1.5"
        >
          <span
            v-for="label in issue.labels.slice(0, 4)"
            :key="label.id"
            class="inline-flex items-center gap-1 rounded-full border px-2 py-1 text-[11px] font-black"
            :style="{
              borderColor: label.color,
              color: label.color,
              backgroundColor: `${label.color}14`,
            }"
          >
            <Tag class="h-3 w-3" />
            {{ label.name }}
          </span>

          <span
            v-if="issue.labels.length > 4"
            class="rounded-full border border-slate-200 bg-slate-50 px-2 py-1 text-[11px] font-black text-slate-400"
          >
            +{{ issue.labels.length - 4 }}
          </span>
        </div>

        <div
          class="mt-3 flex flex-wrap items-center gap-3 text-xs font-bold text-slate-400"
        >
          <span v-if="issue.due_date" class="inline-flex items-center gap-1">
            <CalendarDays class="h-3.5 w-3.5" />
            {{ formatDateTime(issue.due_date) }}
          </span>

          <span
            v-if="issue.checklist_total > 0"
            class="inline-flex items-center gap-1"
          >
            <ListChecks class="h-3.5 w-3.5" />
            {{ issue.checklist_done }}/{{ issue.checklist_total }}
          </span>

          <span class="inline-flex items-center gap-1 text-blue-500">
            Open
            <ExternalLink class="h-3.5 w-3.5" />
          </span>
        </div>

        <div v-if="issue.checklist_total > 0" class="mt-3">
          <div class="h-1.5 overflow-hidden rounded-full bg-slate-100">
            <div
              class="h-full rounded-full bg-slate-900"
              :style="{ width: `${checklistPercent(issue)}%` }"
            ></div>
          </div>
        </div>
      </button>

      <div v-if="canEdit" class="flex shrink-0 flex-col gap-2">
        <select
          v-if="mode === 'backlog'"
          class="rounded-2xl border border-slate-200 bg-slate-50 px-3 py-2 text-xs font-black text-slate-600 outline-none transition focus:border-blue-400"
          @change="onSprintChange"
        >
          <option value="">Move to sprint</option>

          <option v-for="sprint in sprints" :key="sprint.id" :value="sprint.id">
            {{ sprint.name }} — {{ sprint.status }}
          </option>
        </select>

        <button
          v-else
          type="button"
          class="rounded-2xl border border-slate-200 px-3 py-2 text-xs font-black text-slate-600 transition hover:bg-slate-100"
          @click="emit('move-to-backlog', issue)"
        >
          Move to backlog
        </button>
      </div>
    </div>
  </article>
</template>
