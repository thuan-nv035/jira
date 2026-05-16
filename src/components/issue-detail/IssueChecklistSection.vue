<script setup>
import { onBeforeUnmount, onMounted, ref } from "vue";
import {
  Check,
  Circle,
  ListChecks,
  Pencil,
  Plus,
  Trash2
} from "lucide-vue-next";
import { useIssueChecklist } from "../../composables/useIssueChecklist";

const props = defineProps({
  issue: {
    type: Object,
    required: true
  },
  canEdit: {
    type: Boolean,
    default: true
  }
});

const error = ref("");

const {
  checklists,
  checklistLoading,
  checklistSaving,
  newChecklistTitle,
  editingChecklistId,
  editingChecklistTitle,
  checklistTotal,
  checklistDone,
  checklistPercent,
  loadChecklists,
  createChecklist,
  toggleChecklist,
  startEditChecklist,
  cancelEditChecklist,
  saveEditChecklist,
  deleteChecklist,
  onChecklistRealtime
} = useIssueChecklist({ props, error });

onMounted(() => {
  loadChecklists();
  window.addEventListener("jira-checklist-refresh", onChecklistRealtime);
});

onBeforeUnmount(() => {
  window.removeEventListener("jira-checklist-refresh", onChecklistRealtime);
});
</script>

<template>
  <section class="rounded-2xl border border-slate-200 bg-slate-50 p-4">
    <div class="mb-4 flex items-center justify-between gap-3">
      <div class="flex items-center gap-2">
        <ListChecks class="h-5 w-5 text-slate-500" />
        <h3 class="font-black text-slate-950">
          Checklist
        </h3>
      </div>

      <span
        v-if="checklistTotal > 0"
        class="rounded-full bg-white px-3 py-1 text-xs font-black text-slate-600 shadow-sm"
      >
        {{ checklistDone }}/{{ checklistTotal }}
      </span>
    </div>

    <p
      v-if="error"
      class="mb-3 rounded-xl bg-rose-50 px-4 py-3 text-sm font-medium text-rose-700"
    >
      {{ error }}
    </p>

    <div
      v-if="checklistTotal > 0"
      class="mb-4"
    >
      <div class="mb-2 flex items-center justify-between text-xs font-bold text-slate-500">
        <span>Progress</span>
        <span>{{ checklistPercent }}%</span>
      </div>

      <div class="h-2 overflow-hidden rounded-full bg-slate-200">
        <div
          class="h-full rounded-full bg-slate-900 transition-all duration-300"
          :style="{ width: `${checklistPercent}%` }"
        ></div>
      </div>
    </div>

    <form
      v-if="canEdit"
      class="mb-4 flex gap-2"
      @submit.prevent="createChecklist"
    >
      <input
        v-model="newChecklistTitle"
        type="text"
        placeholder="Add checklist item..."
        class="min-w-0 flex-1 rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm font-semibold text-slate-700 outline-none transition focus:border-blue-400"
      />

      <button
        type="submit"
        class="rounded-2xl bg-slate-900 px-4 py-3 text-sm font-black text-white transition hover:bg-slate-800 disabled:opacity-60"
        :disabled="checklistSaving || !newChecklistTitle.trim()"
        title="Add checklist item"
      >
        <Plus class="h-4 w-4" />
      </button>
    </form>

    <div
      v-if="checklistLoading"
      class="rounded-2xl bg-white p-4 text-sm text-slate-500"
    >
      Loading checklist...
    </div>

    <div
      v-else
      class="space-y-2"
    >
      <div
        v-for="item in checklists"
        :key="item.id"
        class="rounded-2xl bg-white p-3 shadow-sm"
      >
        <div class="flex items-start gap-3">
          <button
            type="button"
            :disabled="!canEdit"
            class="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full border transition disabled:cursor-not-allowed disabled:opacity-60"
            :class="item.is_done
              ? 'border-emerald-500 bg-emerald-500 text-white'
              : 'border-slate-300 text-slate-400 hover:border-slate-500'"
            @click="toggleChecklist(item)"
          >
            <Check
              v-if="item.is_done"
              class="h-4 w-4"
            />
            <Circle
              v-else
              class="h-3 w-3"
            />
          </button>

          <div class="min-w-0 flex-1">
            <div
              v-if="editingChecklistId === item.id"
              class="flex gap-2"
            >
              <input
                v-model="editingChecklistTitle"
                type="text"
                class="min-w-0 flex-1 rounded-xl border border-slate-200 px-3 py-2 text-sm font-semibold outline-none focus:border-blue-400"
                @keyup.enter="saveEditChecklist(item)"
                @keyup.esc="cancelEditChecklist"
              />

              <button
                type="button"
                class="rounded-xl bg-slate-900 px-3 py-2 text-xs font-black text-white"
                @click="saveEditChecklist(item)"
              >
                Save
              </button>

              <button
                type="button"
                class="rounded-xl border border-slate-200 px-3 py-2 text-xs font-black text-slate-500"
                @click="cancelEditChecklist"
              >
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

          <div
            v-if="canEdit && editingChecklistId !== item.id"
            class="flex shrink-0 items-center gap-1"
          >
            <button
              type="button"
              class="rounded-xl p-2 text-slate-400 hover:bg-slate-100 hover:text-slate-900"
              title="Edit"
              @click="startEditChecklist(item)"
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

      <p
        v-if="checklists.length === 0"
        class="rounded-2xl bg-white p-4 text-sm text-slate-500"
      >
        No checklist items yet.
      </p>
    </div>
  </section>
</template>
