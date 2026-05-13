<script setup>
import { computed, ref, onMounted } from "vue";
import { Plus } from "lucide-vue-next";
import IssueCard from "./IssueCard.vue";
import { projectApi } from "../services/api";
import { useRoute } from "vue-router";
const props = defineProps({
  column: { type: Object, required: true },
  issues: { type: Array, default: () => [] },
});
const route = useRoute();
const projectId = computed(() => Number(route.params.id));

const emit = defineEmits([
  "create-issue",
  "open-issue",
  "drag-issue",
  "drop-issue",
]);

const isOver = ref(false);
const sortedIssues = computed(() =>
  [...props.issues].sort((a, b) => a.position - b.position),
);
const members = ref([]);
function onDrop() {
  isOver.value = false;
  emit("drop-issue", props.column);
}

const loadProjectMember = async () => {
  try {
    members.value = await projectApi.members(projectId.value);
  } catch (error) {
    console.error("Error loading project members:", error);
  }
};

onMounted(async () => {
  await loadProjectMember();
});
</script>

<template>
  <section
    class="flex min-h-[620px] w-80 shrink-0 flex-col rounded-3xl border border-slate-200 bg-slate-100/80 p-3"
    @dragover.prevent="isOver = true"
    @dragleave="isOver = false"
    @drop.prevent="onDrop"
  >
    <div class="mb-3 flex items-center justify-between px-2 py-1">
      <div>
        <h2 class="text-sm font-black uppercase tracking-wide text-slate-700">
          {{ column.name }}
        </h2>
        <p class="text-xs font-medium text-slate-400">
          {{ sortedIssues.length }} issues
        </p>
      </div>
      <button
        class="rounded-xl bg-white p-2 text-slate-500 shadow-sm transition hover:text-slate-950"
        @click="emit('create-issue', column)"
      >
        <Plus class="h-4 w-4" />
      </button>
    </div>

    <div
      :class="[
        'flex flex-1 flex-col gap-3 rounded-2xl p-1 transition',
        isOver ? 'bg-blue-100/70 ring-2 ring-blue-200' : '',
      ]"
    >
      <IssueCard
        v-for="issue in sortedIssues"
        :key="issue.id"
        :issue="issue"
        :members="members"
        @open="emit('open-issue', issue)"
        @dragstart="emit('drag-issue', issue)"
      />

      <button
        v-if="sortedIssues.length === 0"
        class="mt-2 flex flex-1 items-center justify-center rounded-2xl border border-dashed border-slate-300 bg-white/70 p-6 text-center text-sm font-semibold text-slate-400 transition hover:border-slate-400 hover:text-slate-600"
        @click="emit('create-issue', column)"
      >
        Drop issue here or create a new one
      </button>
    </div>
  </section>
</template>
