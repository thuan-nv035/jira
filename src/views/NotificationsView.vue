<script setup>
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import {
  Bell,
  CheckCheck,
  Inbox,
  Trash2,
  ArrowLeft,
  ExternalLink
} from "lucide-vue-next";
import { getErrorMessage, notificationApi } from "../services/api";

const router = useRouter();

const notifications = ref([]);
const loading = ref(false);
const error = ref("");
const activeFilter = ref("all");

const filteredNotifications = computed(() => {
  if (activeFilter.value === "unread") {
    return notifications.value.filter((item) => !item.is_read);
  }

  return notifications.value;
});

const unreadCount = computed(() => {
  return notifications.value.filter((item) => !item.is_read).length;
});

async function loadNotifications() {
  loading.value = true;
  error.value = "";

  try {
    notifications.value = await notificationApi.list();
  } catch (err) {
    error.value = getErrorMessage(err);
  } finally {
    loading.value = false;
  }
}

async function markRead(notification) {
  if (notification.is_read) return;

  try {
    await notificationApi.markRead(notification.id);
    notification.is_read = true;
  } catch (err) {
    error.value = getErrorMessage(err);
  }
}

async function markAllRead() {
  try {
    await notificationApi.markAllRead();

    notifications.value = notifications.value.map((item) => ({
      ...item,
      is_read: true
    }));
  } catch (err) {
    error.value = getErrorMessage(err);
  }
}

async function deleteNotification(notification) {
  if (!confirm("Delete this notification?")) return;

  try {
    await notificationApi.remove(notification.id);

    notifications.value = notifications.value.filter(
      (item) => item.id !== notification.id
    );
  } catch (err) {
    error.value = getErrorMessage(err);
  }
}

async function openNotification(notification) {
  await markRead(notification);

  if (notification.project_id && notification.issue_id) {
    router.push({
      path: `/projects/${notification.project_id}`,
      query: {
        issueId: notification.issue_id
      }
    });

    return;
  }

  if (notification.project_id) {
    router.push(`/projects/${notification.project_id}`);
    return;
  }
}

function formatTime(value) {
  if (!value) return "";

  return new Date(value).toLocaleString();
}

function getNotificationTypeLabel(type) {
  const labels = {
    USER_MENTIONED: "Mention",
    COMMENT_CREATED: "Comment",
    ISSUE_CREATED: "Issue",
    ISSUE_UPDATED: "Issue updated",
    ISSUE_MOVED: "Issue moved",
    ATTACHMENT_UPLOADED: "Attachment",
    CHECKLIST_CREATED: "Checklist",
    LABEL_CREATED: "Label"
  };

  return labels[type] || type || "Notification";
}

onMounted(loadNotifications);
</script>

<template>
  <main class="min-h-screen bg-slate-50 px-6 py-8">
    <div class="mx-auto max-w-5xl">
      <button
        type="button"
        class="mb-6 inline-flex items-center gap-2 text-sm font-bold text-slate-500 transition hover:text-slate-900"
        @click="router.back()"
      >
        <ArrowLeft class="h-4 w-4" />
        Back
      </button>

      <section class="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
        <div class="mb-6 flex flex-wrap items-center justify-between gap-4">
          <div class="flex items-center gap-3">
            <div class="flex h-12 w-12 items-center justify-center rounded-2xl bg-slate-900 text-white">
              <Bell class="h-6 w-6" />
            </div>

            <div>
              <h1 class="text-2xl font-black text-slate-950">
                Notifications
              </h1>
              <p class="text-sm font-medium text-slate-500">
                {{ unreadCount }} unread notification(s)
              </p>
            </div>
          </div>

          <button
            type="button"
            class="rounded-2xl bg-slate-900 px-4 py-2 text-sm font-black text-white transition hover:bg-slate-800 disabled:opacity-60"
            :disabled="unreadCount === 0"
            @click="markAllRead"
          >
            <CheckCheck class="mr-2 inline h-4 w-4" />
            Mark all as read
          </button>
        </div>

        <div class="mb-5 flex flex-wrap gap-2">
          <button
            type="button"
            class="rounded-2xl px-4 py-2 text-sm font-black transition"
            :class="activeFilter === 'all'
              ? 'bg-slate-900 text-white'
              : 'bg-slate-100 text-slate-600 hover:bg-slate-200'"
            @click="activeFilter = 'all'"
          >
            All
          </button>

          <button
            type="button"
            class="rounded-2xl px-4 py-2 text-sm font-black transition"
            :class="activeFilter === 'unread'
              ? 'bg-slate-900 text-white'
              : 'bg-slate-100 text-slate-600 hover:bg-slate-200'"
            @click="activeFilter = 'unread'"
          >
            Unread
          </button>
        </div>

        <div
          v-if="error"
          class="mb-4 rounded-2xl border border-rose-100 bg-rose-50 p-4 text-sm font-bold text-rose-700"
        >
          {{ error }}
        </div>

        <div
          v-if="loading"
          class="rounded-2xl bg-slate-50 p-5 text-sm font-semibold text-slate-500"
        >
          Loading notifications...
        </div>

        <div
          v-else-if="filteredNotifications.length === 0"
          class="rounded-3xl bg-slate-50 p-10 text-center"
        >
          <Inbox class="mx-auto mb-3 h-10 w-10 text-slate-300" />

          <p class="font-black text-slate-700">
            No notifications
          </p>

          <p class="mt-1 text-sm text-slate-400">
            New updates will appear here.
          </p>
        </div>

        <div v-else class="space-y-3">
          <article
            v-for="notification in filteredNotifications"
            :key="notification.id"
            class="group rounded-3xl border p-4 transition hover:-translate-y-0.5 hover:shadow-sm"
            :class="notification.is_read
              ? 'border-slate-100 bg-white'
              : 'border-blue-100 bg-blue-50'"
          >
            <div class="flex items-start justify-between gap-4">
              <button
                type="button"
                class="min-w-0 flex-1 text-left"
                @click="openNotification(notification)"
              >
                <div class="mb-2 flex flex-wrap items-center gap-2">
                  <span
                    class="rounded-full px-3 py-1 text-xs font-black"
                    :class="notification.is_read
                      ? 'bg-slate-100 text-slate-500'
                      : 'bg-blue-600 text-white'"
                  >
                    {{ getNotificationTypeLabel(notification.type || notification.notification_type) }}
                  </span>

                  <span class="text-xs font-semibold text-slate-400">
                    {{ formatTime(notification.created_at) }}
                  </span>
                </div>

                <h2 class="text-sm font-black text-slate-950">
                  {{ notification.title }}
                </h2>

                <p
                  v-if="notification.message"
                  class="mt-1 line-clamp-2 text-sm font-medium text-slate-500"
                >
                  {{ notification.message }}
                </p>

                <p
                  v-if="notification.project_id || notification.issue_id"
                  class="mt-2 inline-flex items-center gap-1 text-xs font-bold text-blue-600"
                >
                  Open related item
                  <ExternalLink class="h-3.5 w-3.5" />
                </p>
              </button>

              <div class="flex shrink-0 items-center gap-2">
                <button
                  v-if="!notification.is_read"
                  type="button"
                  class="rounded-xl border border-slate-200 px-3 py-2 text-xs font-black text-slate-500 transition hover:bg-slate-100"
                  @click="markRead(notification)"
                >
                  Read
                </button>

                <button
                  type="button"
                  class="rounded-xl border border-rose-200 p-2 text-rose-500 transition hover:bg-rose-50"
                  @click="deleteNotification(notification)"
                >
                  <Trash2 class="h-4 w-4" />
                </button>
              </div>
            </div>
          </article>
        </div>
      </section>
    </div>
  </main>
</template>