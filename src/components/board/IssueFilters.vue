<script setup>
defineProps({
  filters: { type: Object, required: true },
  columns: { type: Array, default: () => [] },
  labels: { type: Array, default: () => [] },
  issuesCount: { type: Number, default: 0 },
  loading: { type: Boolean, default: false },
});

const emit = defineEmits(["clear"]);
</script>

<template>
  <section class="mb-6 rounded-3xl border border-slate-200 bg-white p-4 shadow-sm">
    <div class="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
      <div>
        <label class="mb-1 block text-xs font-bold uppercase tracking-wide text-slate-400">
          Search
        </label>
        <input
          v-model="filters.keyword"
          type="text"
          placeholder="Search title, code, description..."
          class="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-2.5 text-sm font-semibold text-slate-700 outline-none transition focus:border-blue-400 focus:bg-white"
        />
      </div>

      <div>
        <label class="mb-1 block text-xs font-bold uppercase tracking-wide text-slate-400">
          Status
        </label>
        <select
          v-model="filters.column_id"
          class="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-2.5 text-sm font-semibold text-slate-700 outline-none transition focus:border-blue-400 focus:bg-white"
        >
          <option value="">All columns</option>
          <option v-for="column in columns" :key="column.id" :value="column.id">
            {{ column.name }}
          </option>
        </select>
      </div>

      <div>
        <label class="mb-1 block text-xs font-bold uppercase tracking-wide text-slate-400">
          Priority
        </label>
        <select
          v-model="filters.priority"
          class="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-2.5 text-sm font-semibold text-slate-700 outline-none transition focus:border-blue-400 focus:bg-white"
        >
          <option value="">All priorities</option>
          <option value="LOW">Low</option>
          <option value="MEDIUM">Medium</option>
          <option value="HIGH">High</option>
          <option value="URGENT">Urgent</option>
        </select>
      </div>

      <div>
        <label class="mb-1 block text-xs font-bold uppercase tracking-wide text-slate-400">
          Type
        </label>
        <select
          v-model="filters.issue_type"
          class="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-2.5 text-sm font-semibold text-slate-700 outline-none transition focus:border-blue-400 focus:bg-white"
        >
          <option value="">All types</option>
          <option value="TASK">Task</option>
          <option value="BUG">Bug</option>
          <option value="STORY">Story</option>
        </select>
      </div>

      <div>
        <label class="mb-1 block text-xs font-bold uppercase tracking-wide text-slate-400">
          Attachment
        </label>
        <select
          v-model="filters.has_attachment"
          class="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-2.5 text-sm font-semibold text-slate-700 outline-none transition focus:border-blue-400 focus:bg-white"
        >
          <option value="">All</option>
          <option value="true">Has files</option>
          <option value="false">No files</option>
        </select>
      </div>

      <div>
        <label class="mb-1 block text-xs font-bold uppercase tracking-wide text-slate-400">
          Sort
        </label>
        <select
          v-model="filters.sort_by"
          class="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-2.5 text-sm font-semibold text-slate-700 outline-none transition focus:border-blue-400 focus:bg-white"
        >
          <option value="updated_at">Updated</option>
          <option value="created_at">Created</option>
          <option value="priority">Priority</option>
          <option value="title">Title</option>
          <option value="position">Position</option>
        </select>
      </div>

      <div>
        <label class="mb-1 block text-xs font-bold uppercase tracking-wide text-slate-400">
          Deadline
        </label>
        <select
          v-model="filters.overdue"
          class="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-2.5 text-sm font-semibold text-slate-700 outline-none transition focus:border-blue-400 focus:bg-white"
        >
          <option value="">All</option>
          <option value="true">Overdue</option>
          <option value="false">Not overdue</option>
        </select>
      </div>

      <div>
        <label class="mb-1 block text-xs font-bold uppercase tracking-wide text-slate-400">
          Label
        </label>
        <select
          v-model="filters.label_id"
          class="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-2.5 text-sm font-semibold text-slate-700 outline-none transition focus:border-blue-400 focus:bg-white"
        >
          <option value="">All labels</option>
          <option v-for="label in labels" :key="label.id" :value="label.id">
            {{ label.name }}
          </option>
        </select>
      </div>
    </div>

    <div class="mt-4 flex flex-wrap items-center justify-between gap-3">
      <div class="flex items-center gap-3 text-sm text-slate-500">
        <span v-if="loading" class="font-semibold text-blue-600">Filtering...</span>
        <span v-else>
          Showing
          <b class="text-slate-900">{{ issuesCount }}</b>
          issue(s)
        </span>
      </div>

      <div class="flex items-center gap-2">
        <select
          v-model="filters.order"
          class="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-2 text-sm font-semibold text-slate-700 outline-none transition focus:border-blue-400 focus:bg-white"
        >
          <option value="desc">Newest first</option>
          <option value="asc">Oldest first</option>
        </select>

        <button
          type="button"
          class="rounded-2xl border border-slate-200 px-4 py-2 text-sm font-bold text-slate-600 transition hover:bg-slate-100"
          @click="emit('clear')"
        >
          Clear
        </button>
      </div>
    </div>
  </section>
</template>
