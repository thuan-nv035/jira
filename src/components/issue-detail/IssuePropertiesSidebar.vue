<script setup>
import { computed } from "vue";
import IssueLabelsPicker from "./IssueLabelsPicker.vue";
import { normalizeMember } from "../../utils/memberUtils";
const props = defineProps({
  issue: { type: Object, required: true },
  form: { type: Object, required: true },
  members: { type: Array, default: () => [] },
  projectLabels: { type: Array, default: () => [] },
  epics: { type: Array, default: () => [] },
  sprints: { type: Array, default: () => [] },
  canEdit: { type: Boolean, default: true },
  reporter: { type: Object, default: null },
});

const emit = defineEmits(["update-epic", "update-sprint"]);

const normalizedMembers = computed(() => props.members.map(normalizeMember).filter(Boolean));

const selectedEpic = computed(() => {
  if (!props.form.epic_id) return null;
  return props.epics.find((epic) => Number(epic.id) === Number(props.form.epic_id));
});

const selectedSprint = computed(() => {
  if (!props.form.sprint_id) return null;
  return props.sprints.find((sprint) => Number(sprint.id) === Number(props.form.sprint_id));
});

</script>

<template>
  <aside class="space-y-4 rounded-2xl border border-slate-200 bg-white p-4">
    <div>
      <label class="label">Type</label>
      <select v-model="form.issue_type" :disabled="!canEdit" class="input">
        <option value="TASK">TASK</option>
        <option value="BUG">BUG</option>
        <option value="STORY">STORY</option>
      </select>
    </div>

    <div>
      <label class="label">Priority</label>
      <select v-model="form.priority" :disabled="!canEdit" class="input">
        <option value="LOW">LOW</option>
        <option value="MEDIUM">MEDIUM</option>
        <option value="HIGH">HIGH</option>
        <option value="URGENT">URGENT</option>
      </select>
    </div>

    <div>
      <label class="label">Assignee</label>
      <select v-model="form.assignee_id" :disabled="!canEdit" class="input">
        <option value="">Unassigned</option>
        <option v-for="member in normalizedMembers" :key="member.id" :value="member.id">
          {{ member.full_name }}
        </option>
      </select>
    </div>

    <div>
      <label class="mb-2 block text-sm font-bold text-slate-600">Epic</label>
      <select
        v-model="form.epic_id"
        class="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm font-semibold text-slate-700 outline-none transition focus:border-violet-400 disabled:bg-slate-100"
        :disabled="!canEdit"
        @change="emit('update-epic')"
      >
        <option value="">No epic</option>
        <option v-for="epic in epics" :key="epic.id" :value="epic.id">
          {{ epic.name }}
        </option>
      </select>

      <div
        v-if="selectedEpic"
        class="mt-2 inline-flex items-center gap-2 rounded-full border px-3 py-1.5 text-xs font-black"
        :style="{
          borderColor: selectedEpic.color,
          color: selectedEpic.color,
          backgroundColor: `${selectedEpic.color}14`,
        }"
      >
        <span class="h-2 w-2 rounded-full" :style="{ backgroundColor: selectedEpic.color }"></span>
        {{ selectedEpic.name }}
      </div>
    </div>

    <div>
      <label class="mb-2 block text-sm font-bold text-slate-600">Sprint</label>
      <select
        v-model="form.sprint_id"
        class="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm font-semibold text-slate-700 outline-none transition focus:border-blue-400 disabled:bg-slate-100"
        :disabled="!canEdit"
        @change="emit('update-sprint')"
      >
        <option value="">Backlog / No sprint</option>
        <option v-for="sprint in sprints" :key="sprint.id" :value="sprint.id">
          {{ sprint.name }} — {{ sprint.status }}
        </option>
      </select>

      <div
        v-if="selectedSprint"
        class="mt-2 inline-flex items-center gap-2 rounded-full bg-blue-50 px-3 py-1.5 text-xs font-black text-blue-700"
      >
        {{ selectedSprint.name }}
        <span class="rounded-full bg-white px-2 py-0.5 text-[10px]">
          {{ selectedSprint.status }}
        </span>
      </div>
    </div>

    <IssueLabelsPicker
      :issue="issue"
      :project-labels="projectLabels"
      :can-edit="canEdit"
    />

    <div>
      <label class="mb-2 block text-sm font-bold text-slate-600">Due date</label>
      <input
        v-model="form.due_date"
        :disabled="!canEdit"
        type="datetime-local"
        class="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm font-semibold text-slate-700 outline-none transition focus:border-blue-400"
      />

      <p v-if="issue.is_overdue" class="mt-2 text-xs font-bold text-rose-600">
        This task is overdue
      </p>
    </div>

    <div class="rounded-2xl bg-slate-50 p-4 text-sm text-slate-600">
      <div class="mb-3 flex items-center gap-3">
        <div class="flex h-9 w-9 items-center justify-center rounded-full bg-slate-900 text-xs font-black text-white">
          {{ reporter?.full_name?.slice(0, 2).toUpperCase() || "?" }}
        </div>

        <div>
          <p class="text-sm font-black text-slate-800">
            Reporter: {{ reporter?.full_name || "Unknown" }}
          </p>

          <p v-if="reporter?.email" class="text-xs text-slate-400">
            {{ reporter.email }}
          </p>
        </div>
      </div>

      <p>
        <b>Created:</b>
        {{ new Date(issue.created_at).toLocaleDateString() }}
      </p>
      <p>
        <b>Updated:</b>
        {{ new Date(issue.updated_at).toLocaleDateString() }}
      </p>
    </div>
  </aside>
</template>
