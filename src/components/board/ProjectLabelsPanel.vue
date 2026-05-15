<script setup>
defineProps({
  labels: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
  form: { type: Object, required: true },
  canEdit: { type: Boolean, default: false },
});

const emit = defineEmits(["create", "delete"]);
</script>

<template>
  <section class="mb-6 rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
    <div class="mb-4 flex flex-wrap items-center justify-between gap-3">
      <div>
        <h2 class="text-base font-black text-slate-950">Project Labels</h2>
        <p class="text-sm text-slate-500">Create and manage labels used by issues</p>
      </div>

      <span class="rounded-full bg-slate-100 px-3 py-1 text-xs font-black text-slate-500">
        {{ labels.length }} label(s)
      </span>
    </div>

    <form
      v-if="canEdit"
      class="mb-4 grid gap-3 md:grid-cols-[1fr_auto_auto]"
      @submit.prevent="emit('create')"
    >
      <input
        v-model="form.name"
        type="text"
        placeholder="Label name, e.g. Frontend"
        class="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm font-bold text-slate-700 outline-none transition focus:border-blue-400 focus:bg-white"
      />

      <input
        v-model="form.color"
        type="color"
        class="h-12 w-20 cursor-pointer rounded-2xl border border-slate-200 bg-white p-2"
      />

      <button
        type="submit"
        class="rounded-2xl bg-slate-900 px-5 py-3 text-sm font-black text-white transition hover:bg-slate-800 disabled:opacity-60"
        :disabled="!form.name.trim()"
      >
        Add label
      </button>
    </form>

    <div v-if="loading" class="rounded-2xl bg-slate-50 p-4 text-sm font-semibold text-slate-500">
      Loading labels...
    </div>

    <div v-else class="flex flex-wrap gap-2">
      <div
        v-for="label in labels"
        :key="label.id"
        class="group flex items-center gap-2 rounded-full border px-3 py-2 text-sm font-black"
        :style="{
          borderColor: label.color,
          color: label.color,
          backgroundColor: `${label.color}14`,
        }"
      >
        <span>{{ label.name }}</span>

        <button
          v-if="canEdit"
          type="button"
          class="hidden rounded-full px-1 text-xs group-hover:inline"
          title="Delete label"
          @click="emit('delete', label)"
        >
          ×
        </button>
      </div>

      <p
        v-if="labels.length === 0"
        class="rounded-2xl bg-slate-50 p-4 text-sm font-semibold text-slate-500"
      >
        No labels yet.
      </p>
    </div>
  </section>
</template>
