<script setup>
import { onBeforeUnmount, onMounted } from "vue";
import ToastContainer from "./components/ui/ToastContainer.vue";
import { useToast } from "./composables/useToast";

const toast = useToast();

function handleAuthExpired(event) {
  toast.warning(
    event.detail?.message || "Your session has expired. Please login again.",
    "Session expired"
  );
}

onMounted(() => {
  window.addEventListener("jira-auth-expired", handleAuthExpired);
});

onBeforeUnmount(() => {
  window.removeEventListener("jira-auth-expired", handleAuthExpired);
});
</script>

<template>
  <RouterView />
  <ToastContainer />
</template>