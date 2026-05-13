<script setup>
defineProps({
  title: { type: String, default: "No data" },
  description: { type: String, default: "Create your first item to get started." }
});
</script>

<template>
  <div class="flex min-h-64 flex-col items-center justify-center rounded-3xl border border-dashed border-slate-300 bg-white p-8 text-center">
    <div class="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-slate-100 text-2xl">✨</div>
    <h3 class="text-lg font-black text-slate-950">{{ title }}</h3>
    <p class="mt-1 max-w-md text-sm text-slate-500">{{ description }}</p>
    <div class="mt-5">
      <slot />
    </div>
  </div>
</template>
