<script setup>
import { reactive, ref } from "vue";
import ModalShell from "./ModalShell.vue";
import { getErrorMessage, projectApi } from "../services/api";
import { useToast } from "../composables/useToast";
const emit = defineEmits(["close", "created"]);
const toast = useToast();
const loading = ref(false);
const error = ref("");
const form = reactive({
  name: "",
  key: "",
  description: ""
});

function normalizeKey() {
  form.key = form.key.toUpperCase().replace(/[^A-Z0-9_]/g, "").slice(0, 20);
}

async function submit() {
  loading.value = true;
  error.value = "";
  try {
    const project = await projectApi.create({
      name: form.name.trim(),
      key: form.key.trim(),
      description: form.description.trim() || null
    });
    emit("created", project);
  } catch (err) {
    error.value = getErrorMessage(err);
    toast.error(error.value);
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <ModalShell title="Create project" subtitle="" @close="emit('close')">
    <form class="space-y-4" @submit.prevent="submit">
      <div>
        <label class="label">Project name</label>
        <input v-model="form.name" class="input" placeholder="Example: Website Redesign" required />
      </div>
      <div>
        <label class="label">Project key</label>
        <input v-model="form.key" @input="normalizeKey" class="input" placeholder="WEB" required />
        <p class="mt-1 text-xs text-slate-500">Viết hoa, không dấu, ví dụ: WEB, APP, DEMO.</p>
      </div>
      <div>
        <label class="label">Description</label>
        <textarea v-model="form.description" class="input min-h-28 resize-none" placeholder="Short project description"></textarea>
      </div>
      <p v-if="error" class="rounded-xl bg-rose-50 px-4 py-3 text-sm font-medium text-rose-700">{{ error }}</p>
      <div class="flex justify-end gap-3">
        <button type="button" class="btn-secondary" @click="emit('close')">Cancel</button>
        <button class="btn-primary" :disabled="loading">{{ loading ? 'Creating...' : 'Create project' }}</button>
      </div>
    </form>
  </ModalShell>
</template>
