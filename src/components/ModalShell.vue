<script setup>
import { X } from "lucide-vue-next";

defineProps({
  title: { type: String, required: true },
  subtitle: { type: String, default: "" },
  wide: { type: Boolean, default: false }
});

const emit = defineEmits(["close"]);
</script>

<template>
  <div class="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/50 p-4 backdrop-blur-sm">
    <div :class="['max-h-[90vh] w-full overflow-hidden rounded-3xl bg-white shadow-soft', wide ? 'max-w-4xl' : 'max-w-lg']">
      <div class="flex items-start justify-between border-b border-slate-100 px-6 py-5">
        <div>
          <h2 class="text-xl font-black tracking-tight text-slate-950">{{ title }}</h2>
          <p v-if="subtitle" class="mt-1 text-sm text-slate-500">{{ subtitle }}</p>
        </div>
        <button @click="emit('close')" class="rounded-xl p-2 text-slate-400 transition hover:bg-slate-100 hover:text-slate-700">
          <X class="h-5 w-5" />
        </button>
      </div>
      <div class="max-h-[calc(90vh-86px)] overflow-y-auto p-6">
        <slot />
      </div>
    </div>
  </div>
</template>
