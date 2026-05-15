import { ref } from "vue";

const toasts = ref([]);

let toastId = 1;

function removeToast(id) {
  toasts.value = toasts.value.filter((toast) => toast.id !== id);
}

function addToast(payload) {
  const id = toastId++;

  const toast = {
    id,
    type: payload.type || "info",
    title: payload.title || "",
    message: payload.message || "",
    duration: payload.duration ?? 3500
  };

  toasts.value.push(toast);

  if (toast.duration > 0) {
    window.setTimeout(() => {
      removeToast(id);
    }, toast.duration);
  }

  return id;
}

export function useToast() {
  function success(message, title = "Success") {
    return addToast({
      type: "success",
      title,
      message
    });
  }

  function error(message, title = "Error") {
    return addToast({
      type: "error",
      title,
      message,
      duration: 5000
    });
  }

  function info(message, title = "Info") {
    return addToast({
      type: "info",
      title,
      message
    });
  }

  function warning(message, title = "Warning") {
    return addToast({
      type: "warning",
      title,
      message,
      duration: 4500
    });
  }

  return {
    toasts,
    addToast,
    removeToast,
    success,
    error,
    info,
    warning
  };
}