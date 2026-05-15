<script setup>
import { CheckCircle2, AlertCircle, Info, AlertTriangle, X } from "lucide-vue-next";
import { useToast } from "../../composables/useToast";

const { toasts, removeToast } = useToast();

function getToastClass(type) {
  const classes = {
    success: "border-emerald-100 bg-emerald-50 text-emerald-800",
    error: "border-rose-100 bg-rose-50 text-rose-800",
    info: "border-blue-100 bg-blue-50 text-blue-800",
    warning: "border-amber-100 bg-amber-50 text-amber-800"
  };

  return classes[type] || classes.info;
}

function getIcon(type) {
  const icons = {
    success: CheckCircle2,
    error: AlertCircle,
    info: Info,
    warning: AlertTriangle
  };

  return icons[type] || Info;
}
</script>

<template>
  <Teleport to="body">
    <div class="fixed right-5 top-5 z-[9999] flex w-[360px] max-w-[calc(100vw-2rem)] flex-col gap-3">
      <TransitionGroup
        enter-active-class="transition duration-200 ease-out"
        enter-from-class="translate-x-6 opacity-0"
        enter-to-class="translate-x-0 opacity-100"
        leave-active-class="transition duration-150 ease-in"
        leave-from-class="translate-x-0 opacity-100"
        leave-to-class="translate-x-6 opacity-0"
      >
        <div
          v-for="toast in toasts"
          :key="toast.id"
          class="rounded-3xl border p-4 shadow-xl backdrop-blur"
          :class="getToastClass(toast.type)"
        >
          <div class="flex items-start gap-3">
            <component
              :is="getIcon(toast.type)"
              class="mt-0.5 h-5 w-5 shrink-0"
            />

            <div class="min-w-0 flex-1">
              <p class="text-sm font-black">
                {{ toast.title }}
              </p>

              <p
                v-if="toast.message"
                class="mt-1 text-sm font-semibold opacity-80"
              >
                {{ toast.message }}
              </p>
            </div>

            <button
              type="button"
              class="rounded-xl p-1 opacity-60 transition hover:bg-white/60 hover:opacity-100"
              @click="removeToast(toast.id)"
            >
              <X class="h-4 w-4" />
            </button>
          </div>
        </div>
      </TransitionGroup>
    </div>
  </Teleport>
</template>