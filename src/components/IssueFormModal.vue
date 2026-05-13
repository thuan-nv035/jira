<script setup>
import { computed, reactive, ref, watch } from "vue";
import ModalShell from "./ModalShell.vue";
import { getErrorMessage, issueApi } from "../services/api";

const props = defineProps({
  projectId: { type: [String, Number], required: true },
  column: { type: Object, default: null },
  members: { type: Array, default: () => [] }
});

const emit = defineEmits(["close", "created"]);

const loading = ref(false);
const error = ref("");
const form = reactive({
  title: "",
  description: "",
  issue_type: "TASK",
  priority: "MEDIUM",
  assignee_id: "",
  due_date: null
});

const title = computed(() => `Create issue${props.column ? ` in ${props.column.name}` : ''}`);

watch(
  () => props.column,
  () => {
    error.value = "";
  },
  { immediate: true }
);

function fromDatetimeLocal(value) {
  if (!value) return null;

  return new Date(value).toISOString();
}

async function submit() {
  if (!props.column) return;
  loading.value = true;
  error.value = "";
  try {
    const issue = await issueApi.create(props.projectId, {
      column_id: props.column.id,
      title: form.title.trim(),
      description: form.description.trim() || null,
      issue_type: form.issue_type,
      priority: form.priority,
      assignee_id: form.assignee_id ? Number(form.assignee_id) : null,
      due_date: fromDatetimeLocal(form.due_date),
    });
    emit("created", issue);
  } catch (err) {
    error.value = getErrorMessage(err);
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <ModalShell :title="title" subtitle="Tạo task, bug hoặc story cho bảng Kanban." @close="emit('close')">
    <form class="space-y-4" @submit.prevent="submit">
      <div>
        <label class="label">Title</label>
        <input v-model="form.title" class="input" placeholder="Example: Build login page" required />
      </div>

      <div>
        <label class="label">Description</label>
        <textarea v-model="form.description" class="input min-h-28 resize-none" placeholder="Issue details"></textarea>
      </div>

      <div class="grid gap-4 sm:grid-cols-2">
        <div>
          <label class="label">Type</label>
          <select v-model="form.issue_type" class="input">
            <option value="TASK">TASK</option>
            <option value="BUG">BUG</option>
            <option value="STORY">STORY</option>
          </select>
        </div>
        <div>
          <label class="label">Priority</label>
          <select v-model="form.priority" class="input">
            <option value="LOW">LOW</option>
            <option value="MEDIUM">MEDIUM</option>
            <option value="HIGH">HIGH</option>
            <option value="URGENT">URGENT</option>
          </select>
        </div>
      </div>

      <div>
        <label class="label">Assignee</label>
        <select v-model="form.assignee_id" class="input">
          <option value="">Unassigned</option>
          <option v-for="member in members" :key="member.user_id" :value="member.user_id">
            {{ member.user.full_name }} - {{ member.user.email }}
          </option>
        </select>
      </div>

      <div>
        <label class="mb-2 block text-sm font-bold text-slate-600">
            Due date
          </label>

          <input
            v-model="form.due_date"
            type="datetime-local"
            class="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm font-semibold text-slate-700 outline-none transition focus:border-blue-400"
          />
      </div>

      <p v-if="error" class="rounded-xl bg-rose-50 px-4 py-3 text-sm font-medium text-rose-700">{{ error }}</p>

      <div class="flex justify-end gap-3">
        <button type="button" class="btn-secondary" @click="emit('close')">Cancel</button>
        <button class="btn-primary" :disabled="loading">{{ loading ? 'Creating...' : 'Create issue' }}</button>
      </div>
    </form>
  </ModalShell>
</template>
