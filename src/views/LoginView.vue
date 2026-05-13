<script setup>
import { reactive, ref } from "vue";
import { useRouter } from "vue-router";
import { KanbanSquare } from "lucide-vue-next";
import { authApi, getErrorMessage } from "../services/api";

const router = useRouter();
const loading = ref(false);
const error = ref("");
const form = reactive({
  email: "admin@gmail.com",
  password: "123456"
});

async function submit() {
  loading.value = true;
  error.value = "";
  try {
    await authApi.login(form.email, form.password);
    router.push({ name: "projects" });
  } catch (err) {
    error.value = getErrorMessage(err);
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <div class="flex min-h-screen bg-slate-950 p-4">
    <div class="m-auto grid w-full max-w-6xl overflow-hidden rounded-[2rem] bg-white shadow-soft lg:grid-cols-[1.05fr_0.95fr]">
      <section class="hidden bg-gradient-to-br from-slate-950 via-slate-900 to-blue-950 p-10 text-white lg:block">
        <div class="flex h-full flex-col justify-between">
          <div>
            <div class="mb-8 flex h-14 w-14 items-center justify-center rounded-2xl bg-white/10 backdrop-blur">
              <KanbanSquare class="h-7 w-7" />
            </div>
            <h1 class="max-w-lg text-5xl font-black leading-tight tracking-tight">Plan, track and ship work faster.</h1>
            <p class="mt-5 max-w-md text-base leading-7 text-slate-300">
              Jira clone mini dùng Vue, Tailwind và WebSocket realtime. Phù hợp để học cách nối frontend với FastAPI.
            </p>
          </div>
          <div class="grid grid-cols-3 gap-3">
            <div class="rounded-2xl bg-white/10 p-4 backdrop-blur">
              <p class="text-2xl font-black">4</p>
              <p class="text-xs text-slate-300">Default columns</p>
            </div>
            <div class="rounded-2xl bg-white/10 p-4 backdrop-blur">
              <p class="text-2xl font-black">JWT</p>
              <p class="text-xs text-slate-300">Authentication</p>
            </div>
            <div class="rounded-2xl bg-white/10 p-4 backdrop-blur">
              <p class="text-2xl font-black">WS</p>
              <p class="text-xs text-slate-300">Realtime board</p>
            </div>
          </div>
        </div>
      </section>

      <section class="flex min-h-[680px] items-center justify-center p-6 sm:p-10">
        <div class="w-full max-w-md">
          <div class="mb-8 lg:hidden">
            <div class="mb-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-slate-900 text-white">
              <KanbanSquare class="h-6 w-6" />
            </div>
          </div>
          <p class="text-sm font-black uppercase tracking-[0.2em] text-blue-600">Welcome back</p>
          <h2 class="mt-2 text-3xl font-black tracking-tight text-slate-950">Login to your board</h2>
          <p class="mt-2 text-sm text-slate-500">Dùng tài khoản đã đăng ký ở backend FastAPI.</p>

          <form class="mt-8 space-y-4" @submit.prevent="submit">
            <div>
              <label class="label">Email</label>
              <input v-model="form.email" type="email" class="input" required />
            </div>
            <div>
              <label class="label">Password</label>
              <input v-model="form.password" type="password" class="input" required />
            </div>
            <p v-if="error" class="rounded-xl bg-rose-50 px-4 py-3 text-sm font-medium text-rose-700">{{ error }}</p>
            <button class="btn-primary w-full" :disabled="loading">{{ loading ? 'Logging in...' : 'Login' }}</button>
          </form>

          <p class="mt-6 text-center text-sm text-slate-500">
            No account?
            <RouterLink class="font-bold text-slate-950 hover:underline" to="/register">Create one</RouterLink>
          </p>
        </div>
      </section>
    </div>
  </div>
</template>
