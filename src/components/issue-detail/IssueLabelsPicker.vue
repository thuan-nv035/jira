<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from "vue";
import { getErrorMessage, labelApi } from "../../services/api";
import { useToast } from "../../composables/useToast";
const props = defineProps({
  issue: { type: Object, required: true },
  projectLabels: { type: Array, default: () => [] },
  canEdit: { type: Boolean, default: true },
});
const toast = useToast();
const issueLabels = ref([]);
const loading = ref(false);
const error = ref("");

const availableLabels = computed(() => {
  const selectedIds = new Set(issueLabels.value.map((label) => Number(label.id)));
  return props.projectLabels.filter((label) => !selectedIds.has(Number(label.id)));
});

async function loadIssueLabels() {
  loading.value = true;
  error.value = "";

  try {
    issueLabels.value = await labelApi.listIssueLabels(props.issue.id);
  } catch (err) {
    error.value = getErrorMessage(err);
  } finally {
    loading.value = false;
  }
}

async function addLabel(labelId) {
  if (!labelId || !props.canEdit) return;

  try {
    issueLabels.value = await labelApi.addToIssue(props.issue.id, labelId);
  } catch (err) {
    error.value = getErrorMessage(err);
    toast.error(error.value);
  }
}

async function removeLabel(label) {
  if (!props.canEdit) return;

  try {
    await labelApi.removeFromIssue(props.issue.id, label.id);
    issueLabels.value = issueLabels.value.filter((item) => Number(item.id) !== Number(label.id));
  } catch (err) {
    error.value = getErrorMessage(err);
    toast.error(error.value);
  }
}

function onRealtime(event) {
  const issueId = Number(event.detail?.issue_id);
  if (!issueId || issueId === Number(props.issue.id)) loadIssueLabels();
}

onMounted(() => {
  loadIssueLabels();
  window.addEventListener("jira-label-refresh", onRealtime);
});

onBeforeUnmount(() => {
  window.removeEventListener("jira-label-refresh", onRealtime);
});
</script>

<template>
  <div>
    <label class="mb-2 block text-sm font-bold text-slate-600">Labels</label>

    <div v-if="loading" class="rounded-2xl bg-slate-50 p-3 text-sm text-slate-500">
      Loading labels...
    </div>

    <div v-else class="space-y-3">
      <p v-if="error" class="rounded-xl bg-rose-50 px-4 py-3 text-sm font-medium text-rose-700">
        {{ error }}
      </p>

      <div class="flex flex-wrap gap-2">
        <span
          v-for="label in issueLabels"
          :key="label.id"
          class="group inline-flex items-center gap-2 rounded-full border px-3 py-1.5 text-xs font-black"
          :style="{
            borderColor: label.color,
            color: label.color,
            backgroundColor: `${label.color}14`,
          }"
        >
          {{ label.name }}

          <button
            v-if="canEdit"
            type="button"
            class="rounded-full px-1 opacity-70 transition hover:opacity-100"
            title="Remove label"
            @click="removeLabel(label)"
          >
            ×
          </button>
        </span>

        <span v-if="issueLabels.length === 0" class="text-sm font-semibold text-slate-400">
          No labels
        </span>
      </div>

      <select
        v-if="canEdit"
        class="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm font-semibold text-slate-700 outline-none transition focus:border-blue-400"
        @change="addLabel($event.target.value); $event.target.value = ''"
      >
        <option value="">Add label...</option>
        <option v-for="label in availableLabels" :key="label.id" :value="label.id">
          {{ label.name }}
        </option>
      </select>
    </div>
  </div>
</template>
