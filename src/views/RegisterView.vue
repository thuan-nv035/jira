<script setup>
import { reactive, ref } from "vue";
import { useRouter } from "vue-router";
import { KanbanSquare } from "lucide-vue-next";
import { authApi, getErrorMessage } from "../services/api";

const router = useRouter();
const loading = ref(false);
const error = ref("");
const form = reactive({
  full_name: "Admin User",
  email: "admin@gmail.com",
  password: "123456",
});

async function submit() {
  loading.value = true;
  error.value = "";
  try {
    await authApi.register(form);
    router.push({ name: "projects" });
  } catch (err) {
    error.value = getErrorMessage(err);
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <div class="flex min-h-screen items-center justify-center bg-slate-950 p-4">
    <div class="w-full max-w-md rounded-[2rem] bg-white p-8 shadow-soft">
      <div
        class="mb-6 flex h-14 w-14 items-center justify-center rounded-2xl bg-slate-900 text-white"
      >
        <KanbanSquare class="h-7 w-7" />
      </div>
      <p class="text-sm font-black uppercase tracking-[0.2em] text-blue-600">
        Create account
      </p>
      <h1 class="mt-2 text-3xl font-black tracking-tight text-slate-950">
        Start your workspace
      </h1>
      <p class="mt-2 text-sm text-slate-500">
        Tạo tài khoản để dùng API Jira clone.
      </p>

      <form class="mt-8 space-y-4" @submit.prevent="submit">
        <div>
          <label class="label">Full name</label>
          <input v-model="form.full_name" class="input" required />
        </div>
        <div>
          <label class="label">Email</label>
          <input v-model="form.email" type="email" class="input" required />
        </div>
        <div>
          <label class="label">Password</label>
          <input
            v-model="form.password"
            type="password"
            class="input"
            minlength="6"
            required
          />
        </div>
        <p
          v-if="error"
          class="rounded-xl bg-rose-50 px-4 py-3 text-sm font-medium text-rose-700"
        >
          {{ error }}
        </p>
        <button class="btn-primary w-full" :disabled="loading">
          {{ loading ? "Creating..." : "Register" }}
        </button>
      </form>

      <p class="mt-6 text-center text-sm text-slate-500">
        Already have account?
        <RouterLink class="font-bold text-slate-950 hover:underline" to="/login"
          >Login</RouterLink
        >
      </p>
    </div>
  </div>
</template>
