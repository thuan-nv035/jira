<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { Bell, CheckCheck, Inbox, Loader2, Trash2 } from "lucide-vue-next";
import { getErrorMessage, notificationApi } from "../services/api";

const router = useRouter();
const open = ref(false);
const loading = ref(false);
const error = ref("");
const notifications = ref([]);
const unreadCount = ref(0);
let pollingTimer = null;

const hasUnread = computed(() => unreadCount.value > 0);

function formatTime(value) {
  if (!value) return "";
  return new Intl.DateTimeFormat("en", {
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

async function loadUnreadCount() {
  try {
    const data = await notificationApi.unreadCount();
    unreadCount.value = data.unread_count || 0;
  } catch {
    // Keep UI quiet if token is missing during logout.
  }
}

async function loadNotifications() {
  loading.value = true;
  error.value = "";
  try {
    notifications.value = await notificationApi.list({ limit: 30 });
    await loadUnreadCount();
  } catch (err) {
    error.value = getErrorMessage(err);
  } finally {
    loading.value = false;
  }
}

async function togglePanel() {
  open.value = !open.value;
  if (open.value) {
    await loadNotifications();
  }
}

async function refreshFromRealtime() {
  await loadUnreadCount();
  if (open.value) {
    await loadNotifications();
  }
}

async function markAllRead() {
  await notificationApi.markAllRead();
  notifications.value = notifications.value.map((item) => ({
    ...item,
    is_read: true,
  }));
  unreadCount.value = 0;
}

async function openNotification(notification) {
  if (!notification.is_read) {
    const updated = await notificationApi.markRead(notification.id);
    notifications.value = notifications.value.map((item) =>
      item.id === updated.id ? updated : item,
    );
    unreadCount.value = Math.max(0, unreadCount.value - 1);
  }

  open.value = false;
  if (notification.project_id) {
    router.push(`/projects/${notification.project_id}/board`);
  }
}

async function removeNotification(notification) {
  await notificationApi.remove(notification.id);
  notifications.value = notifications.value.filter(
    (item) => item.id !== notification.id,
  );
  if (!notification.is_read) {
    unreadCount.value = Math.max(0, unreadCount.value - 1);
  }
}

function closeWhenClickOutside(event) {
  if (!event.target.closest?.("[data-notification-root]")) {
    open.value = false;
  }
}

onMounted(() => {
  loadUnreadCount();
  pollingTimer = setInterval(loadUnreadCount, 20000);
  window.addEventListener("jira-notification-refresh", refreshFromRealtime);
  window.addEventListener("click", closeWhenClickOutside);
});

onBeforeUnmount(() => {
  if (pollingTimer) clearInterval(pollingTimer);
  window.removeEventListener("jira-notification-refresh", refreshFromRealtime);
  window.removeEventListener("click", closeWhenClickOutside);
});
</script>

<template>
  <div data-notification-root class="relative">
    <button
      class="relative inline-flex h-10 w-10 items-center justify-center rounded-xl border border-slate-200 bg-white text-slate-700 shadow-sm transition hover:bg-slate-50"
      title="Notifications"
      @click.stop="togglePanel"
    >
      <Bell class="h-4 w-4" />
      <span
        v-if="hasUnread"
        class="absolute -right-1 -top-1 flex min-h-5 min-w-5 items-center justify-center rounded-full bg-rose-600 px-1 text-[10px] font-black text-white ring-2 ring-white"
      >
        {{ unreadCount > 9 ? "9+" : unreadCount }}
      </span>
    </button>

    <div
      v-if="open"
      class="absolute right-0 top-12 z-50 w-[360px] overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-2xl"
    >
      <div
        class="flex items-center justify-between border-b border-slate-100 px-4 py-3"
      >
        <div>
          <p class="text-sm font-black text-slate-950">Notifications</p>
          <p class="text-xs text-slate-500">{{ unreadCount }} unread</p>
        </div>
        <button
          class="inline-flex items-center gap-1.5 rounded-xl px-3 py-2 text-xs font-bold text-slate-600 hover:bg-slate-100"
          @click="markAllRead"
        >
          <CheckCheck class="h-3.5 w-3.5" /> Mark all
        </button>
      </div>

      <div
        v-if="loading"
        class="flex items-center justify-center gap-2 px-4 py-10 text-sm font-semibold text-slate-500"
      >
        <Loader2 class="h-4 w-4 animate-spin" /> Loading notifications...
      </div>

      <p
        v-else-if="error"
        class="m-4 rounded-2xl bg-rose-50 px-4 py-3 text-sm font-semibold text-rose-700"
      >
        {{ error }}
      </p>

      <div
        v-else-if="notifications.length === 0"
        class="px-4 py-10 text-center"
      >
        <div
          class="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-slate-100 text-slate-400"
        >
          <Inbox class="h-5 w-5" />
        </div>
        <p class="mt-3 text-sm font-bold text-slate-900">
          No notifications yet
        </p>
        <p class="mt-1 text-xs text-slate-500">
          Issue updates, comments and member changes will appear here.
        </p>
      </div>

      <div v-else class="max-h-[440px] overflow-y-auto p-2">
        <div
          v-for="notification in notifications"
          :key="notification.id"
          :class="[
            'group flex cursor-pointer gap-3 rounded-2xl px-3 py-3 transition hover:bg-slate-50',
            notification.is_read ? 'bg-white' : 'bg-blue-50/70',
          ]"
          @click="openNotification(notification)"
        >
          <span
            :class="[
              'mt-1 h-2.5 w-2.5 shrink-0 rounded-full',
              notification.is_read ? 'bg-slate-200' : 'bg-blue-600',
            ]"
          ></span>
          <div class="min-w-0 flex-1">
            <p class="line-clamp-1 text-sm font-black text-slate-950">
              {{ notification.title }}
            </p>
            <p class="mt-1 line-clamp-2 text-xs leading-5 text-slate-500">
              {{ notification.message || notification.type }}
            </p>
            <div class="mt-2 flex items-center justify-between gap-2">
              <span
                class="text-[11px] font-bold uppercase tracking-wide text-slate-400"
                >{{ notification.type.replaceAll("_", " ") }}</span
              >
              <span class="text-[11px] font-semibold text-slate-400">{{
                formatTime(notification.created_at)
              }}</span>
            </div>
          </div>
          <button
            class="hidden h-8 w-8 shrink-0 items-center justify-center rounded-xl text-slate-400 hover:bg-white hover:text-rose-600 group-hover:flex"
            title="Delete"
            @click.stop="removeNotification(notification)"
          >
            <Trash2 class="h-3.5 w-3.5" />
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
