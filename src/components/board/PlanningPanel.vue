<script setup>
defineProps({
  epics: { type: Array, default: () => [] },
  sprints: { type: Array, default: () => [] },
  epicForm: { type: Object, required: true },
  sprintForm: { type: Object, required: true },
  epicLoading: { type: Boolean, default: false },
  sprintLoading: { type: Boolean, default: false },
  canEdit: { type: Boolean, default: false },
});

const emit = defineEmits(["create-epic", "delete-epic", "create-sprint", "delete-sprint"]);
</script>

<template>
  <section class="mb-6 grid gap-6 xl:grid-cols-2">
    <div class="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
      <div class="mb-4 flex items-center justify-between gap-3">
        <div>
          <h2 class="text-base font-black text-slate-950">Epics</h2>
          <p class="text-sm text-slate-500">Group related issues into larger goals</p>
        </div>

        <span class="rounded-full bg-violet-50 px-3 py-1 text-xs font-black text-violet-700">
          {{ epics.length }} epic(s)
        </span>
      </div>

      <form
        v-if="canEdit"
        class="mb-4 grid gap-3 md:grid-cols-[1fr_auto_auto]"
        @submit.prevent="emit('create-epic')"
      >
        <input
          v-model="epicForm.name"
          type="text"
          placeholder="Epic name"
          class="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm font-bold outline-none focus:border-violet-400"
        />

        <input
          v-model="epicForm.color"
          type="color"
          class="h-12 w-20 cursor-pointer rounded-2xl border border-slate-200 bg-white p-2"
        />

        <button
          type="submit"
          class="rounded-2xl bg-violet-600 px-5 py-3 text-sm font-black text-white hover:bg-violet-700 disabled:opacity-60"
          :disabled="!epicForm.name.trim()"
        >
          Add epic
        </button>
      </form>

      <textarea
        v-if="canEdit"
        v-model="epicForm.description"
        rows="2"
        placeholder="Epic description..."
        class="mb-4 w-full resize-none rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm font-semibold outline-none focus:border-violet-400"
      ></textarea>

      <div v-if="epicLoading" class="rounded-2xl bg-slate-50 p-4 text-sm font-semibold text-slate-500">
        Loading epics...
      </div>

      <div v-else class="space-y-3">
        <div
          v-for="epic in epics"
          :key="epic.id"
          class="flex items-center justify-between gap-3 rounded-2xl border border-slate-100 bg-slate-50 p-4"
        >
          <div class="min-w-0">
            <div class="flex items-center gap-2">
              <span class="h-3 w-3 rounded-full" :style="{ backgroundColor: epic.color }"></span>
              <p class="truncate text-sm font-black text-slate-900">{{ epic.name }}</p>
            </div>

            <p v-if="epic.description" class="mt-1 line-clamp-1 text-xs font-semibold text-slate-400">
              {{ epic.description }}
            </p>
          </div>

          <button
            v-if="canEdit"
            type="button"
            class="rounded-xl border border-rose-200 px-3 py-2 text-xs font-black text-rose-500 hover:bg-rose-50"
            @click="emit('delete-epic', epic)"
          >
            Delete
          </button>
        </div>

        <p v-if="epics.length === 0" class="rounded-2xl bg-slate-50 p-4 text-sm font-semibold text-slate-500">
          No epics yet.
        </p>
      </div>
    </div>

    <div class="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
      <div class="mb-4 flex items-center justify-between gap-3">
        <div>
          <h2 class="text-base font-black text-slate-950">Sprints</h2>
          <p class="text-sm text-slate-500">Plan issues into working cycles</p>
        </div>

        <span class="rounded-full bg-blue-50 px-3 py-1 text-xs font-black text-blue-700">
          {{ sprints.length }} sprint(s)
        </span>
      </div>

      <form
        v-if="canEdit"
        class="mb-4 grid gap-3 md:grid-cols-2"
        @submit.prevent="emit('create-sprint')"
      >
        <input
          v-model="sprintForm.name"
          type="text"
          placeholder="Sprint name"
          class="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm font-bold outline-none focus:border-blue-400"
        />

        <select
          v-model="sprintForm.status"
          class="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm font-bold outline-none focus:border-blue-400"
        >
          <option value="PLANNED">PLANNED</option>
          <option value="ACTIVE">ACTIVE</option>
          <option value="COMPLETED">COMPLETED</option>
        </select>

        <input
          v-model="sprintForm.start_date"
          type="datetime-local"
          class="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm font-bold outline-none focus:border-blue-400"
        />

        <input
          v-model="sprintForm.end_date"
          type="datetime-local"
          class="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm font-bold outline-none focus:border-blue-400"
        />

        <textarea
          v-model="sprintForm.goal"
          rows="2"
          placeholder="Sprint goal..."
          class="resize-none rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm font-semibold outline-none focus:border-blue-400 md:col-span-2"
        ></textarea>

        <button
          type="submit"
          class="rounded-2xl bg-blue-600 px-5 py-3 text-sm font-black text-white hover:bg-blue-700 disabled:opacity-60 md:col-span-2"
          :disabled="!sprintForm.name.trim()"
        >
          Add sprint
        </button>
      </form>

      <div v-if="sprintLoading" class="rounded-2xl bg-slate-50 p-4 text-sm font-semibold text-slate-500">
        Loading sprints...
      </div>

      <div v-else class="space-y-3">
        <div
          v-for="sprint in sprints"
          :key="sprint.id"
          class="flex items-center justify-between gap-3 rounded-2xl border border-slate-100 bg-slate-50 p-4"
        >
          <div class="min-w-0">
            <div class="flex items-center gap-2">
              <span
                class="rounded-full px-2 py-1 text-[11px] font-black"
                :class="sprint.status === 'ACTIVE'
                  ? 'bg-emerald-50 text-emerald-700'
                  : sprint.status === 'COMPLETED'
                    ? 'bg-slate-200 text-slate-600'
                    : 'bg-blue-50 text-blue-700'"
              >
                {{ sprint.status }}
              </span>

              <p class="truncate text-sm font-black text-slate-900">{{ sprint.name }}</p>
            </div>

            <p v-if="sprint.goal" class="mt-1 line-clamp-1 text-xs font-semibold text-slate-400">
              {{ sprint.goal }}
            </p>
          </div>

          <button
            v-if="canEdit"
            type="button"
            class="rounded-xl border border-rose-200 px-3 py-2 text-xs font-black text-rose-500 hover:bg-rose-50"
            @click="emit('delete-sprint', sprint)"
          >
            Delete
          </button>
        </div>

        <p v-if="sprints.length === 0" class="rounded-2xl bg-slate-50 p-4 text-sm font-semibold text-slate-500">
          No sprints yet.
        </p>
      </div>
    </div>
  </section>
</template>
