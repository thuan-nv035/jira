<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from "vue";
import { Check, Circle, ListChecks, Pencil, Plus, Trash2 } from "lucide-vue-next";
import { checklistApi, getErrorMessage } from "../../services/api";

const props = defineProps({
  issue: { type: Object, required: true },
  canEdit: { type: Boolean, default: true },
});

const checklists = ref([]);
const loading = ref(false);
const saving = ref(false);
const error = ref("");
const newTitle = ref("");
const editingId = ref(null);
const editingTitle = ref("");

const total = computed(() => checklists.value.length);
const done = computed(() => checklists.value.filter((item) => item.is_done).length);
const percent = computed(() => (total.value ? Math.round((done.value * 100) / total.value) : 0));

async function loadChecklists() {
  loading.value = true;
  error.value = "";

  try {
    checklists.value = await checklistApi.list(props.issue.id);
  } catch (err) {
    error.value = getErrorMessage(err);
  } finally {
    loading.value = false;
  }
}

async function createChecklist() {
  const title = newTitle.value.trim();
  if (!title) return;

  saving.value = true;
  error.value = "";

  try {
    await checklistApi.create(props.issue.id, { title });
    newTitle.value = "";
    await loadChecklists();
  } catch (err) {
    error.value = getErrorMessage(err);
  } finally {
    saving.value = false;
  }
}

async function toggleChecklist(item) {
  if (!props.canEdit) return;

  const nextValue = !item.is_done;
  item.is_done = nextValue;

  try {
    await checklistApi.update(item.id, { is_done: nextValue });
    await loadChecklists();
  } catch (err) {
    item.is_done = !nextValue;
    error.value = getErrorMessage(err);
  }
}

function startEdit(item) {
  editingId.value = item.id;
  editingTitle.value = item.title;
}

function cancelEdit() {
  editingId.value = null;
  editingTitle.value = "";
}

async function saveEdit(item) {
  const title = editingTitle.value.trim();
  if (!title) {
    error.value = "Checklist title is required";
    return;
  }

  try {
    await checklistApi.update(item.id, { title });
    cancelEdit();
    await loadChecklists();
  } catch (err) {
    error.value = getErrorMessage(err);
  }
}

async function deleteChecklist(item) {
  if (!confirm(`Delete checklist "${item.title}"?`)) return;

  try {
    await checklistApi.remove(item.id);
    checklists.value = checklists.value.filter((checklist) => checklist.id !== item.id);
  } catch (err) {
    error.value = getErrorMessage(err);
  }
}

function onRealtime(event) {
  const issueId = Number(event.detail?.issue_id);
  if (issueId === Number(props.issue.id)) loadChecklists();
}

onMounted(() => {
  loadChecklists();
  window.addEventListener("jira-checklist-refresh", onRealtime);
});

onBeforeUnmount(() => {
  window.removeEventListener("jira-checklist-refresh", onRealtime);
});
</script>

<template>
  <section class="rounded-2xl border border-slate-200 bg-slate-50 p-4">
    <div class="mb-4 flex items-center justify-between gap-3">
      <div class="flex items-center gap-2">
        <ListChecks class="h-5 w-5 text-slate-500" />
        <h3 class="font-black text-slate-950">Checklist</h3>
      </div>

      <span
        v-if="total > 0"
        class="rounded-full bg-white px-3 py-1 text-xs font-black text-slate-600 shadow-sm"
      >
        {{ done }}/{{ total }}
      </span>
    </div>

    <p v-if="error" class="mb-3 rounded-xl bg-rose-50 px-4 py-3 text-sm font-medium text-rose-700">
      {{ error }}
    </p>

    <div v-if="total > 0" class="mb-4">
      <div class="mb-2 flex items-center justify-between text-xs font-bold text-slate-500">
        <span>Progress</span>
        <span>{{ percent }}%</span>
      </div>

      <div class="h-2 overflow-hidden rounded-full bg-slate-200">
        <div
          class="h-full rounded-full bg-slate-900 transition-all duration-300"
          :style="{ width: `${percent}%` }"
        ></div>
      </div>
    </div>

    <form v-if="canEdit" class="mb-4 flex gap-2" @submit.prevent="createChecklist">
      <input
        v-model="newTitle"
        type="text"
        placeholder="Add checklist item..."
        class="min-w-0 flex-1 rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm font-semibold text-slate-700 outline-none transition focus:border-blue-400"
      />

      <button
        type="submit"
        class="rounded-2xl bg-slate-900 px-4 py-3 text-sm font-black text-white transition hover:bg-slate-800 disabled:opacity-60"
        :disabled="saving || !newTitle.trim()"
      >
        <Plus class="h-4 w-4" />
      </button>
    </form>

    <div v-if="loading" class="rounded-2xl bg-white p-4 text-sm text-slate-500">
      Loading checklist...
    </div>

    <div v-else class="space-y-2">
      <div
        v-for="item in checklists"
        :key="item.id"
        class="rounded-2xl bg-white p-3 shadow-sm"
      >
        <div class="flex items-start gap-3">
          <button
            type="button"
            :disabled="!canEdit"
            class="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full border transition"
            :class="item.is_done ? 'border-emerald-500 bg-emerald-500 text-white' : 'border-slate-300 text-slate-400 hover:border-slate-500'"
            @click="toggleChecklist(item)"
          >
            <Check v-if="item.is_done" class="h-4 w-4" />
            <Circle v-else class="h-3 w-3" />
          </button>

          <div class="min-w-0 flex-1">
            <div v-if="editingId === item.id" class="flex gap-2">
              <input
                v-model="editingTitle"
                type="text"
                class="min-w-0 flex-1 rounded-xl border border-slate-200 px-3 py-2 text-sm font-semibold outline-none focus:border-blue-400"
                @keyup.enter="saveEdit(item)"
                @keyup.esc="cancelEdit"
              />

              <button type="button" class="rounded-xl bg-slate-900 px-3 py-2 text-xs font-black text-white" @click="saveEdit(item)">
                Save
              </button>

              <button type="button" class="rounded-xl border border-slate-200 px-3 py-2 text-xs font-black text-slate-500" @click="cancelEdit">
                Cancel
              </button>
            </div>

            <p
              v-else
              class="text-sm font-bold text-slate-800"
              :class="item.is_done ? 'text-slate-400 line-through' : ''"
            >
              {{ item.title }}
            </p>
          </div>

          <div v-if="canEdit && editingId !== item.id" class="flex shrink-0 items-center gap-1">
            <button
              type="button"
              class="rounded-xl p-2 text-slate-400 hover:bg-slate-100 hover:text-slate-900"
              title="Edit"
              @click="startEdit(item)"
            >
              <Pencil class="h-4 w-4" />
            </button>

            <button
              type="button"
              class="rounded-xl p-2 text-rose-400 hover:bg-rose-50 hover:text-rose-600"
              title="Delete"
              @click="deleteChecklist(item)"
            >
              <Trash2 class="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>

      <p v-if="checklists.length === 0" class="rounded-2xl bg-white p-4 text-sm text-slate-500">
        No checklist items yet.
      </p>
    </div>
  </section>
</template>
