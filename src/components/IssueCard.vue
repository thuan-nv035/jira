<script setup>
import {
  Bug,
  CheckSquare,
  Layers3,
  Paperclip,
  CalendarDays,
  AlertTriangle,
  ListChecks,
} from "lucide-vue-next";
import { computed } from "vue";
const props = defineProps({
  issue: {
    type: Object,
    required: true,
  },
  members: {
    type: Array,
    default: () => [],
  },
});
const emit = defineEmits(["open", "dragstart"]);

const checklistProgress = computed(() => {
  const total = Number(props.issue.checklist_total || 0);
  const done = Number(props.issue.checklist_done || 0);

  if (total === 0) return 0;

  return Math.round((done * 100) / total);
});

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

const assignee = computed(() => {
  if (!props.issue.assignee_id) return null;

  return props.members
    .map(normalizeMember)
    .find((member) => Number(member.id) === Number(props.issue.assignee_id));
});

function normalizeMember(member) {
  if (!member) return null;

  if (member.user) {
    return {
      id: member.user.id,
      full_name: member.user.full_name || member.user.email || "User",
      email: member.user.email || "",
      avatar_url: member.user.avatar_url || "",
    };
  }

  return {
    id: member.id || member.user_id,
    full_name: member.full_name || member.email || "User",
    email: member.email || "",
    avatar_url: member.avatar_url || "",
  };
}

function getInitials(name) {
  if (!name) return "?";

  const words = name.trim().split(/\s+/);

  if (words.length === 1) {
    return words[0].slice(0, 2).toUpperCase();
  }

  return `${words[0][0]}${words[words.length - 1][0]}`.toUpperCase();
}

function getAvatarColor(name) {
  const colors = [
    "bg-blue-600",
    "bg-violet-600",
    "bg-emerald-600",
    "bg-amber-500",
    "bg-rose-600",
    "bg-cyan-600",
    "bg-indigo-600",
    "bg-fuchsia-600",
    "bg-slate-700",
  ];

  const text = name || "User";
  const index = text.charCodeAt(0) % colors.length;

  return colors[index];
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
      v-if="issue.labels && issue.labels.length > 0"
      class="mt-3 flex flex-wrap gap-1.5"
    >
      <span
        v-for="label in issue.labels.slice(0, 3)"
        :key="label.id"
        class="rounded-full border px-2 py-1 text-[11px] font-black"
        :style="{
          borderColor: label.color,
          color: label.color,
          backgroundColor: `${label.color}14`,
        }"
      >
        {{ label.name }}
      </span>

      <span
        v-if="issue.labels.length > 3"
        class="rounded-full border border-slate-200 bg-slate-50 px-2 py-1 text-[11px] font-black text-slate-400"
      >
        +{{ issue.labels.length - 3 }}
      </span>
    </div>

    <div v-if="issue.checklist_total > 0" class="mt-3">
      <div
        class="mb-1 flex items-center justify-between text-[11px] font-bold text-slate-400"
      >
        <span>Checklist</span>
        <span>{{ checklistProgress }}%</span>
      </div>

      <div class="h-1.5 overflow-hidden rounded-full bg-slate-100">
        <div
          class="h-full rounded-full bg-slate-900 transition-all duration-300"
          :style="{ width: `${checklistProgress}%` }"
        ></div>
      </div>
    </div>

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
          v-if="issue.checklist_total > 0"
          class="flex items-center gap-1 rounded-full border border-slate-100 bg-slate-50 px-2 py-1 text-xs font-black text-slate-600"
          title="Checklist progress"
        >
          <ListChecks class="h-3.5 w-3.5" />
          {{ issue.checklist_done }}/{{ issue.checklist_total }}
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

      <div class="group relative shrink-0">
        <div
          v-if="assignee"
          class="flex h-8 w-8 items-center justify-center overflow-hidden rounded-full border-2 border-white text-xs font-black text-white shadow-sm ring-1 ring-slate-200 transition hover:scale-110"
          :class="
            !assignee.avatar_url ? getAvatarColor(assignee.full_name) : ''
          "
        >
          <img
            v-if="assignee.avatar_url"
            :src="assignee.avatar_url"
            :alt="assignee.full_name"
            class="h-full w-full object-cover"
          />

          <span v-else>
            {{ getInitials(assignee.full_name) }}
          </span>
        </div>

        <div
          v-else
          class="flex h-8 w-8 items-center justify-center rounded-full border-2 border-white bg-slate-100 text-xs font-black text-slate-400 shadow-sm ring-1 ring-slate-200"
        >
          ?
        </div>

        <div
          class="pointer-events-none absolute bottom-10 right-0 z-50 hidden w-max max-w-56 rounded-xl bg-slate-950 px-3 py-2 text-xs font-bold text-white shadow-xl group-hover:block"
        >
          <template v-if="assignee">
            {{ assignee.full_name }}
            <div
              v-if="assignee.email"
              class="mt-0.5 text-[11px] font-medium text-slate-300"
            >
              {{ assignee.email }}
            </div>
          </template>

          <template v-else> Unassigned </template>
        </div>
      </div>
    </div>
  </article>
</template>
