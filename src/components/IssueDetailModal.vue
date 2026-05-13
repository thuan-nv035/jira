<script setup>
import { computed, onMounted, reactive, ref } from "vue";
import { MessageCircle, Save, Trash2 } from "lucide-vue-next";
import ModalShell from "./ModalShell.vue";
import { commentApi, getErrorMessage, issueApi } from "../services/api";
import { getUser } from "../utils/storage";

const props = defineProps({
  projectId: { type: [String, Number], required: true },
  issue: { type: Object, required: true },
  members: { type: Array, default: () => [] }
});

const emit = defineEmits(["close", "changed", "deleted"]);

const currentUser = getUser();
const loading = ref(false);
const deleting = ref(false);
const error = ref("");
const comments = ref([]);
const commentText = ref("");
const commentLoading = ref(false);

const form = reactive({
  title: props.issue.title,
  description: props.issue.description || "",
  issue_type: props.issue.issue_type,
  priority: props.issue.priority,
  assignee_id: props.issue.assignee_id || ""
});

const assigneeName = computed(() => {
  const member = props.members.find((item) => item.user_id === props.issue.assignee_id);
  return member?.user?.full_name || "Unassigned";
});

async function loadComments() {
  comments.value = await commentApi.list(props.issue.id);
}

async function saveIssue() {
  loading.value = true;
  error.value = "";
  try {
    const updated = await issueApi.update(props.projectId, props.issue.id, {
      title: form.title.trim(),
      description: form.description.trim() || null,
      issue_type: form.issue_type,
      priority: form.priority,
      assignee_id: form.assignee_id ? Number(form.assignee_id) : null
    });
    emit("changed", updated);
  } catch (err) {
    error.value = getErrorMessage(err);
  } finally {
    loading.value = false;
  }
}

async function deleteIssue() {
  if (!confirm("Delete this issue?")) return;
  deleting.value = true;
  error.value = "";
  try {
    await issueApi.remove(props.projectId, props.issue.id);
    emit("deleted", props.issue.id);
  } catch (err) {
    error.value = getErrorMessage(err);
  } finally {
    deleting.value = false;
  }
}

async function addComment() {
  if (!commentText.value.trim()) return;
  commentLoading.value = true;
  error.value = "";
  try {
    await commentApi.create(props.issue.id, { body: commentText.value.trim() });
    commentText.value = "";
    await loadComments();
  } catch (err) {
    error.value = getErrorMessage(err);
  } finally {
    commentLoading.value = false;
  }
}

onMounted(loadComments);
</script>

<template>
  <ModalShell :title="issue.code" :subtitle="`Assigned to ${assigneeName}`" wide @close="emit('close')">
    <div class="grid gap-6 lg:grid-cols-[1fr_320px]">
      <div class="space-y-4">
        <div>
          <label class="label">Title</label>
          <input v-model="form.title" class="input text-base font-bold" />
        </div>

        <div>
          <label class="label">Description</label>
          <textarea v-model="form.description" class="input min-h-44 resize-none"></textarea>
        </div>

        <p v-if="error" class="rounded-xl bg-rose-50 px-4 py-3 text-sm font-medium text-rose-700">{{ error }}</p>

        <div class="flex flex-wrap gap-3">
          <button class="btn-primary" :disabled="loading" @click="saveIssue">
            <Save class="h-4 w-4" />
            {{ loading ? 'Saving...' : 'Save changes' }}
          </button>
          <button class="btn-danger" :disabled="deleting" @click="deleteIssue">
            <Trash2 class="h-4 w-4" />
            {{ deleting ? 'Deleting...' : 'Delete' }}
          </button>
        </div>

        <section class="rounded-2xl border border-slate-200 bg-slate-50 p-4">
          <div class="mb-4 flex items-center gap-2">
            <MessageCircle class="h-5 w-5 text-slate-500" />
            <h3 class="font-black text-slate-950">Comments</h3>
          </div>

          <form class="mb-4 flex gap-2" @submit.prevent="addComment">
            <input v-model="commentText" class="input" placeholder="Write a comment..." />
            <button class="btn-primary whitespace-nowrap" :disabled="commentLoading">Send</button>
          </form>

          <div class="space-y-3">
            <div v-for="comment in comments" :key="comment.id" class="rounded-2xl bg-white p-4 shadow-sm">
              <div class="mb-1 flex items-center justify-between gap-2">
                <p class="text-sm font-black text-slate-900">{{ comment.author.full_name }}</p>
                <p class="text-xs text-slate-400">{{ new Date(comment.created_at).toLocaleString() }}</p>
              </div>
              <p class="text-sm leading-6 text-slate-600">{{ comment.body }}</p>
            </div>
            <p v-if="comments.length === 0" class="rounded-2xl bg-white p-4 text-sm text-slate-500">No comments yet.</p>
          </div>
        </section>
      </div>

      <aside class="space-y-4 rounded-2xl border border-slate-200 bg-white p-4">
        <div>
          <label class="label">Type</label>
          <select v-model="form.issue_type" class="input">
            <option value="TASK">TASK</option>
            <option value="BUG">BUG</option>
            <option value="STORY">STORY</option>
          </select>
        </div>
        <div>
          <label class="label">Priority</label>
          <select v-model="form.priority" class="input">
            <option value="LOW">LOW</option>
            <option value="MEDIUM">MEDIUM</option>
            <option value="HIGH">HIGH</option>
            <option value="URGENT">URGENT</option>
          </select>
        </div>
        <div>
          <label class="label">Assignee</label>
          <select v-model="form.assignee_id" class="input">
            <option value="">Unassigned</option>
            <option v-for="member in members" :key="member.user_id" :value="member.user_id">
              {{ member.user.full_name }}
            </option>
          </select>
        </div>
        <div class="rounded-2xl bg-slate-50 p-4 text-sm text-slate-600">
          <p><b>Reporter ID:</b> {{ issue.reporter_id || currentUser?.id }}</p>
          <p><b>Created:</b> {{ new Date(issue.created_at).toLocaleDateString() }}</p>
          <p><b>Updated:</b> {{ new Date(issue.updated_at).toLocaleDateString() }}</p>
        </div>
      </aside>
    </div>
  </ModalShell>
</template>
