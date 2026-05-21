<script setup>
import {
  Check,
  Circle,
  ListChecks,
  Pencil,
  Plus,
  Save,
  Trash2,
  X
} from "lucide-vue-next";

defineProps({
  subtasks: {
    type: Array,
    default: () => []
  },
  subtaskLoading: {
    type: Boolean,
    default: false
  },
  subtaskSaving: {
    type: Boolean,
    default: false
  },
  subtaskTotal: {
    type: Number,
    default: 0
  },
  subtaskDone: {
    type: Number,
    default: 0
  },
  subtaskPercent: {
    type: Number,
    default: 0
  },
  newSubtaskTitle: {
    type: String,
    default: ""
  },
  newSubtaskAssigneeId: {
    type: [String, Number],
    default: ""
  },
  editingSubtaskId: {
    type: [String, Number, null],
    default: null
  },
  editingSubtaskTitle: {
    type: String,
    default: ""
  },
  editingSubtaskAssigneeId: {
    type: [String, Number],
    default: ""
  },
  assigneeOptions: {
    type: Array,
    default: () => []
  },
  canEdit: {
    type: Boolean,
    default: true
  },
  getSubtaskAssigneeName: {
    type: Function,
    required: true
  }
});

const emit = defineEmits([
  "update:newSubtaskTitle",
  "update:newSubtaskAssigneeId",
  "update:editingSubtaskTitle",
  "update:editingSubtaskAssigneeId",
  "create",
  "toggle",
  "start-edit",
  "cancel-edit",
  "save-edit",
  "delete"
]);
</script>

<template>
  <section class="rounded-2xl border border-slate-200 bg-slate-50 p-4">
    <div class="mb-4 flex items-center justify-between gap-3">
      <div class="flex items-center gap-2">
        <ListChecks class="h-5 w-5 text-slate-500" />

        <div>
          <h3 class="font-black text-slate-950">
            Subtasks
          </h3>

          <p class="text-xs font-semibold text-slate-400">
            {{ subtaskDone }}/{{ subtaskTotal }} completed
          </p>
        </div>
      </div>

      <span class="rounded-full bg-white px-3 py-1 text-xs font-black text-slate-500">
        {{ subtaskPercent }}%
      </span>
    </div>

    <div class="mb-4 h-2 overflow-hidden rounded-full bg-white">
      <div
        class="h-full rounded-full bg-slate-900 transition-all"
        :style="{ width: `${subtaskPercent}%` }"
      ></div>
    </div>

    <form
      v-if="canEdit"
      class="mb-4 grid gap-2 md:grid-cols-[1fr_180px_auto]"
      @submit.prevent="emit('create')"
    >
      <input
        :value="newSubtaskTitle"
        type="text"
        placeholder="Add a subtask..."
        class="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm font-semibold text-slate-700 outline-none transition focus:border-blue-400"
        @input="emit('update:newSubtaskTitle', $event.target.value)"
      />

      <select
        :value="newSubtaskAssigneeId"
        class="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm font-semibold text-slate-700 outline-none transition focus:border-blue-400"
        @change="emit('update:newSubtaskAssigneeId', $event.target.value)"
      >
        <option value="">Unassigned</option>

        <option
          v-for="member in assigneeOptions"
          :key="member.id"
          :value="member.id"
        >
          {{ member.full_name }}
        </option>
      </select>

      <button
        type="submit"
        class="rounded-2xl bg-slate-900 px-4 py-3 text-sm font-black text-white transition hover:bg-slate-800 disabled:opacity-60"
        :disabled="subtaskSaving || !newSubtaskTitle.trim()"
      >
        <Plus class="mr-1 inline h-4 w-4" />
        Add
      </button>
    </form>

    <div
      v-if="subtaskLoading"
      class="rounded-2xl bg-white p-4 text-sm font-semibold text-slate-500"
    >
      Loading subtasks...
    </div>

    <div
      v-else-if="subtasks.length === 0"
      class="rounded-2xl bg-white p-4 text-sm font-semibold text-slate-400"
    >
      No subtasks yet.
    </div>

    <div
      v-else
      class="space-y-2"
    >
      <article
        v-for="subtask in subtasks"
        :key="subtask.id"
        class="rounded-2xl bg-white p-3 shadow-sm"
      >
        <div
          v-if="editingSubtaskId === subtask.id"
          class="grid gap-2 md:grid-cols-[1fr_180px_auto_auto]"
        >
          <input
            :value="editingSubtaskTitle"
            type="text"
            class="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-2.5 text-sm font-semibold text-slate-700 outline-none focus:border-blue-400"
            @input="emit('update:editingSubtaskTitle', $event.target.value)"
            @keydown.enter.prevent="emit('save-edit', subtask)"
          />

          <select
            :value="editingSubtaskAssigneeId"
            class="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-2.5 text-sm font-semibold text-slate-700 outline-none focus:border-blue-400"
            @change="emit('update:editingSubtaskAssigneeId', $event.target.value)"
          >
            <option value="">Unassigned</option>

            <option
              v-for="member in assigneeOptions"
              :key="member.id"
              :value="member.id"
            >
              {{ member.full_name }}
            </option>
          </select>

          <button
            type="button"
            class="rounded-2xl bg-slate-900 px-3 py-2 text-xs font-black text-white"
            @click="emit('save-edit', subtask)"
          >
            <Save class="mr-1 inline h-3.5 w-3.5" />
            Save
          </button>

          <button
            type="button"
            class="rounded-2xl border border-slate-200 px-3 py-2 text-xs font-black text-slate-500"
            @click="emit('cancel-edit')"
          >
            <X class="mr-1 inline h-3.5 w-3.5" />
            Cancel
          </button>
        </div>

        <div
          v-else
          class="flex items-start justify-between gap-3"
        >
          <button
            type="button"
            class="mt-0.5 shrink-0 text-slate-400 transition hover:text-emerald-600 disabled:cursor-not-allowed disabled:opacity-50"
            :disabled="!canEdit"
            @click="emit('toggle', subtask)"
          >
            <Check
              v-if="subtask.is_done"
              class="h-5 w-5 rounded-full bg-emerald-500 p-0.5 text-white"
            />

            <Circle
              v-else
              class="h-5 w-5"
            />
          </button>

          <div class="min-w-0 flex-1">
            <p
              class="text-sm font-black"
              :class="subtask.is_done
                ? 'text-slate-400 line-through'
                : 'text-slate-900'"
            >
              {{ subtask.title }}
            </p>

            <p class="mt-1 text-xs font-semibold text-slate-400">
              Assigned to {{ getSubtaskAssigneeName(subtask) }}
            </p>
          </div>

          <div
            v-if="canEdit"
            class="flex shrink-0 items-center gap-1"
          >
            <button
              type="button"
              class="rounded-xl border border-slate-200 p-2 text-slate-500 transition hover:bg-slate-50"
              @click="emit('start-edit', subtask)"
            >
              <Pencil class="h-3.5 w-3.5" />
            </button>

            <button
              type="button"
              class="rounded-xl border border-rose-200 p-2 text-rose-500 transition hover:bg-rose-50"
              @click="emit('delete', subtask)"
            >
              <Trash2 class="h-3.5 w-3.5" />
            </button>
          </div>
        </div>
      </article>
    </div>
  </section>
</template>