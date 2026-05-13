<script setup>
import {
  Bug,
  CheckSquare,
  Layers3,
  Paperclip,
  CalendarDays,
  AlertTriangle,
} from "lucide-vue-next";

const props = defineProps({
  issue: { type: Object, required: true },
});

const emit = defineEmits(["open", "dragstart"]);

function priorityClass(priority) {
  return (
    {
      LOW: "bg-emerald-50 text-emerald-700 ring-emerald-100",
      MEDIUM: "bg-blue-50 text-blue-700 ring-blue-100",
      HIGH: "bg-amber-50 text-amber-700 ring-amber-100",
      URGENT: "bg-rose-50 text-rose-700 ring-rose-100",
    }[priority] || "bg-slate-50 text-slate-700 ring-slate-100"
  );
}

function TypeIcon(type) {
  return type === "BUG" ? Bug : type === "STORY" ? Layers3 : CheckSquare;
}

function formatDueDate(value) {
  if (!value) return "";

  return new Date(value).toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
  });
}

function dueDateClass(issue) {
  if (!issue.due_date) return "";

  if (issue.is_overdue) {
    return "bg-rose-50 text-rose-700 border-rose-100";
  }

  return "bg-slate-50 text-slate-600 border-slate-100";
}
</script>

<template>
  <article
    draggable="true"
    @dragstart="emit('dragstart', issue)"
    @click="emit('open', issue)"
    class="group cursor-pointer rounded-2xl border border-slate-200 bg-white p-4 shadow-sm transition hover:-translate-y-0.5 hover:border-slate-300 hover:shadow-md"
  >
    <div class="mb-3 flex items-center justify-between gap-2">
      <span class="text-xs font-black uppercase tracking-wide text-slate-400">{{
        issue.code
      }}</span>
      <span
        :class="[
          'rounded-full px-2.5 py-1 text-[11px] font-black ring-1',
          priorityClass(issue.priority),
        ]"
      >
        {{ issue.priority }}
      </span>
    </div>

    <h3 class="line-clamp-2 text-sm font-extrabold leading-5 text-slate-950">
      {{ issue.title }}
    </h3>
    <p
      v-if="issue.description"
      class="mt-2 line-clamp-2 text-xs leading-5 text-slate-500"
    >
      {{ issue.description }}
    </p>

    <div
      class="mt-4 flex items-center justify-between border-t border-slate-100 pt-3"
    >
      <div class="flex flex-wrap items-center gap-2">
        <div
          class="flex items-center gap-1.5 text-xs font-semibold text-slate-500"
        >
          <component :is="TypeIcon(issue.issue_type)" class="h-4 w-4" />
          {{ issue.issue_type }}
        </div>

        <div
          v-if="issue.attachment_count > 0"
          class="flex items-center gap-1 text-xs font-bold text-slate-400"
          title="Attachments"
        >
          <Paperclip class="h-3.5 w-3.5" />
          {{ issue.attachment_count }}
        </div>

        <div
          v-if="issue.due_date"
          class="flex items-center gap-1 rounded-full border px-2 py-1 text-xs font-black"
          :class="dueDateClass(issue)"
          title="Due date"
        >
          <AlertTriangle v-if="issue.is_overdue" class="h-3.5 w-3.5" />
          <CalendarDays v-else class="h-3.5 w-3.5" />
          {{ formatDueDate(issue.due_date) }}
        </div>
      </div>

      <div
        class="flex h-7 w-7 items-center justify-center rounded-full bg-slate-900 text-xs font-black text-white"
      >
        {{ issue.assignee_id || issue.reporter_id || "?" }}
      </div>
    </div>
  </article>
</template>
