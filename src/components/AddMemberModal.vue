<script setup>
import { reactive, ref } from "vue";
import ModalShell from "./ModalShell.vue";
import { getErrorMessage, projectApi } from "../services/api";
import { useToast } from "../composables/useToast";
const toast = useToast();
const props = defineProps({
  projectId: { type: [String, Number], required: true }
});

const emit = defineEmits(["close", "added"]);

const loading = ref(false);
const error = ref("");
const form = reactive({ email: "", role: "MEMBER" });

async function submit() {
  loading.value = true;
  error.value = "";
  try {
    const member = await projectApi.addMember(props.projectId, {
      email: form.email.trim(),
      role: form.role
    });
    emit("added", member);
  } catch (err) {
    error.value = getErrorMessage(err);
    toast.error(error.value);
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <ModalShell title="Add member" subtitle="User phải đăng ký tài khoản trước thì mới add được vào project." @close="emit('close')">
    <form class="space-y-4" @submit.prevent="submit">
      <div>
        <label class="label">Email</label>
        <input v-model="form.email" type="email" class="input" placeholder="member@gmail.com" required />
      </div>
      <div>
        <label class="label">Role</label>
        <select v-model="form.role" class="input">
          <option value="MEMBER">MEMBER</option>
          <option value="ADMIN">ADMIN</option>
        </select>
      </div>
      <p v-if="error" class="rounded-xl bg-rose-50 px-4 py-3 text-sm font-medium text-rose-700">{{ error }}</p>
      <div class="flex justify-end gap-3">
        <button type="button" class="btn-secondary" @click="emit('close')">Cancel</button>
        <button class="btn-primary" :disabled="loading">{{ loading ? 'Adding...' : 'Add member' }}</button>
      </div>
    </form>
  </ModalShell>
</template>
