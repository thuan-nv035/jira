<script setup>
defineProps({
  issueTotal: { type: Number, default: 0 },
  doneTotal: { type: Number, default: 0 },
  membersCount: { type: Number, default: 0 },
});
</script>

<template>
  <div class="mb-5 grid gap-4 md:grid-cols-3">
    <div class="card p-5">
      <p class="text-sm font-semibold text-slate-500">Total issues</p>
      <p class="mt-2 text-3xl font-black text-slate-950">{{ issueTotal }}</p>
    </div>

    <div class="card p-5">
      <p class="text-sm font-semibold text-slate-500">Done</p>
      <p class="mt-2 text-3xl font-black text-slate-950">{{ doneTotal }}</p>
    </div>

    <div class="card p-5">
      <p class="text-sm font-semibold text-slate-500">Members</p>
      <p class="mt-2 text-3xl font-black text-slate-950">{{ membersCount }}</p>
    </div>
  </div>
</template>
