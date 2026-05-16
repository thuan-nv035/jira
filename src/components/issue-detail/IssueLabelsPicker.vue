<script setup>
import { onBeforeUnmount, onMounted, ref } from "vue";
import { useIssueLabels } from "../../composables/useIssueLabels";

const props = defineProps({
  issue: {
    type: Object,
    required: true,
  },
  projectLabels: {
    type: Array,
    default: () => [],
  },
  canEdit: {
    type: Boolean,
    default: true,
  },
});

const error = ref("");

const {
  issueLabels,
  labelLoading,
  availableLabels,
  loadIssueLabels,
  addLabelToIssue,
  removeLabelFromIssue,
  onLabelRealtime,
} = useIssueLabels({
  props,
  error,
});

function handleAddLabel(event) {
  addLabelToIssue(event.target.value);
  event.target.value = "";
}

onMounted(() => {
  loadIssueLabels();
  window.addEventListener("jira-label-refresh", onLabelRealtime);
});

onBeforeUnmount(() => {
  window.removeEventListener("jira-label-refresh", onLabelRealtime);
});
</script>

<template>
  <div>
    <label class="mb-2 block text-sm font-bold text-slate-600">
      Labels
    </label>

    <div
      v-if="labelLoading"
      class="rounded-2xl bg-slate-50 p-3 text-sm text-slate-500"
    >
      Loading labels...
    </div>

    <div v-else class="space-y-3">
      <p
        v-if="error"
        class="rounded-xl bg-rose-50 px-4 py-3 text-sm font-medium text-rose-700"
      >
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
            @click="removeLabelFromIssue(label)"
          >
            ×
          </button>
        </span>

        <span
          v-if="issueLabels.length === 0"
          class="text-sm font-semibold text-slate-400"
        >
          No labels
        </span>
      </div>

      <select
        v-if="canEdit"
        class="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm font-semibold text-slate-700 outline-none transition focus:border-blue-400"
        @change="handleAddLabel"
      >
        <option value="">Add label...</option>

        <option
          v-for="label in availableLabels"
          :key="label.id"
          :value="label.id"
        >
          {{ label.name }}
        </option>
      </select>
    </div>
  </div>
</template>
