<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref } from "vue";
import {
  MessageCircle,
  Save,
  Trash2,
  Paperclip,
  Upload,
  Download,
  X,
  Eye,
  File as FileIcon,
  Image,
  FileText,
  FileArchive,
  FileSpreadsheet,
  FileCode,
  ListChecks,
  Plus,
  Check,
  Pencil,
  Circle,
} from "lucide-vue-next";
import ModalShell from "./ModalShell.vue";
import {
  attachmentApi,
  commentApi,
  getErrorMessage,
  issueApi,
  checklistApi,
} from "../services/api";
import { getUser } from "../utils/storage";

const props = defineProps({
  projectId: { type: [String, Number], required: true },
  issue: { type: Object, required: true },
  members: { type: Array, default: () => [] },
});

const emit = defineEmits(["close", "changed", "deleted"]);

const currentUser = getUser();
const loading = ref(false);
const deleting = ref(false);
const error = ref("");
const comments = ref([]);
const commentText = ref("");
const commentLoading = ref(false);
const attachments = ref([]);
const attachmentInput = ref(null);
const attachmentLoading = ref(false);
const uploadingAttachment = ref(false);
const isDraggingFile = ref(false);
const uploadProgress = ref(0);
const uploadingFileNames = ref([]);
const checklists = ref([]);
const checklistLoading = ref(false);
const checklistSaving = ref(false);
const newChecklistTitle = ref("");
const editingChecklistId = ref(null);
const editingChecklistTitle = ref("");
const form = reactive({
  title: props.issue.title,
  description: props.issue.description || "",
  issue_type: props.issue.issue_type,
  priority: props.issue.priority,
  assignee_id: props.issue.assignee_id || "",
  due_date: toDatetimeLocal(props.issue.due_date),
});

const assigneeName = computed(() => {
  const member = props.members.find(
    (item) => item.user_id === props.issue.assignee_id,
  );
  return member?.user?.full_name || "Unassigned";
});

async function loadComments() {
  comments.value = await commentApi.list(props.issue.id);
}

async function loadChecklists() {
  checklistLoading.value = true;

  try {
    checklists.value = await checklistApi.list(props.issue.id);
  } catch (err) {
    error.value = getErrorMessage(err);
  } finally {
    checklistLoading.value = false;
  }
}

async function createChecklist() {
  const title = newChecklistTitle.value.trim();

  if (!title) return;

  checklistSaving.value = true;
  error.value = "";

  try {
    await checklistApi.create(props.issue.id, {
      title,
    });

    newChecklistTitle.value = "";
    await loadChecklists();
  } catch (err) {
    error.value = getErrorMessage(err);
  } finally {
    checklistSaving.value = false;
  }
}

async function toggleChecklist(item) {
  try {
    const nextValue = !item.is_done;

    item.is_done = nextValue;

    await checklistApi.update(item.id, {
      is_done: nextValue,
    });

    await loadChecklists();
  } catch (err) {
    item.is_done = !item.is_done;
    error.value = getErrorMessage(err);
  }
}

function startEditChecklist(item) {
  editingChecklistId.value = item.id;
  editingChecklistTitle.value = item.title;
}

function cancelEditChecklist() {
  editingChecklistId.value = null;
  editingChecklistTitle.value = "";
}

async function saveEditChecklist(item) {
  const title = editingChecklistTitle.value.trim();

  if (!title) {
    error.value = "Checklist title is required";
    return;
  }

  try {
    await checklistApi.update(item.id, {
      title,
    });

    editingChecklistId.value = null;
    editingChecklistTitle.value = "";
    await loadChecklists();
  } catch (err) {
    error.value = getErrorMessage(err);
  }
}

async function deleteChecklist(item) {
  if (!confirm(`Delete checklist "${item.title}"?`)) return;

  try {
    await checklistApi.remove(item.id);
    checklists.value = checklists.value.filter(
      (checklist) => checklist.id !== item.id,
    );
  } catch (err) {
    error.value = getErrorMessage(err);
  }
}

function onChecklistRealtime(event) {
  const issueId = Number(event.detail?.issue_id);

  if (issueId === Number(props.issue.id)) {
    loadChecklists();
  }
}

async function saveIssue() {
  loading.value = true;
  error.value = "";
  try {
    const updated = await issueApi.update(
      props.issue.project_id,
      props.issue.id,
      {
        title: form.title,
        description: form.description,
        issue_type: form.issue_type,
        priority: form.priority,
        assignee_id: form.assignee_id || null,
        due_date: fromDatetimeLocal(form.due_date),
      },
    );
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

async function loadAttachments() {
  attachmentLoading.value = true;
  try {
    attachments.value = await attachmentApi.list(props.issue.id);
  } catch (err) {
    error.value = getErrorMessage(err);
  } finally {
    attachmentLoading.value = false;
  }
}

async function uploadFiles(files) {
  const selectedFiles = Array.from(files || []);

  if (selectedFiles.length === 0) return;

  if (selectedFiles.length > 10) {
    error.value = "You can upload up to 10 files at once";
    return;
  }

  const oversizedFile = selectedFiles.find(
    (file) => file.size > 10 * 1024 * 1024,
  );

  if (oversizedFile) {
    error.value = `File "${oversizedFile.name}" must be less than 10MB`;
    return;
  }

  uploadingAttachment.value = true;
  uploadProgress.value = 0;
  uploadingFileNames.value = selectedFiles.map((file) => file.name);
  error.value = "";

  try {
    const updateProgress = (percent) => {
      uploadProgress.value = percent;
    };

    if (selectedFiles.length === 1) {
      await attachmentApi.upload(
        props.issue.id,
        selectedFiles[0],
        updateProgress,
      );
    } else {
      await attachmentApi.uploadMany(
        props.issue.id,
        selectedFiles,
        updateProgress,
      );
    }

    uploadProgress.value = 100;
    await loadAttachments();
  } catch (err) {
    error.value = getErrorMessage(err);
  } finally {
    setTimeout(() => {
      uploadingAttachment.value = false;
      uploadProgress.value = 0;
      uploadingFileNames.value = [];
    }, 600);
  }
}

async function uploadAttachment(event) {
  await uploadFiles(event.target.files);
  event.target.value = "";
}

async function handleFileDrop(event) {
  event.preventDefault();
  isDraggingFile.value = false;

  const files = event.dataTransfer?.files;
  await uploadFiles(files);
}

function canPreview(attachment) {
  const type = attachment.content_type || "";

  return (
    type.startsWith("image/") ||
    type === "application/pdf" ||
    type.startsWith("text/")
  );
}

async function previewAttachment(attachment) {
  try {
    const blob = await attachmentApi.preview(props.issue.id, attachment.id);
    const url = window.URL.createObjectURL(blob);

    window.open(url, "_blank");

    setTimeout(() => {
      window.URL.revokeObjectURL(url);
    }, 60 * 1000);
  } catch (err) {
    error.value = getErrorMessage(err);
  }
}

async function downloadAttachment(attachment) {
  try {
    const blob = await attachmentApi.download(props.issue.id, attachment.id);
    const url = window.URL.createObjectURL(blob);

    const link = document.createElement("a");
    link.href = url;
    link.download = attachment.original_name;
    document.body.appendChild(link);
    link.click();

    link.remove();
    window.URL.revokeObjectURL(url);
  } catch (err) {
    error.value = getErrorMessage(err);
  }
}

async function deleteAttachment(attachment) {
  if (!confirm(`Delete file "${attachment.original_name}"?`)) return;

  try {
    await attachmentApi.remove(props.issue.id, attachment.id);
    attachments.value = attachments.value.filter(
      (item) => item.id !== attachment.id,
    );
  } catch (err) {
    error.value = getErrorMessage(err);
  }
}

function formatFileSize(bytes) {
  if (!bytes) return "0 B";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

function getAttachmentIcon(attachment) {
  const type = attachment.content_type || "";
  const name = attachment.original_name?.toLowerCase() || "";

  if (type.startsWith("image/")) return Image;

  if (type === "application/pdf") return FileText;

  if (
    type.includes("spreadsheet") ||
    name.endsWith(".xls") ||
    name.endsWith(".xlsx") ||
    name.endsWith(".csv")
  ) {
    return FileSpreadsheet;
  }

  if (
    type.includes("zip") ||
    type.includes("rar") ||
    type.includes("7z") ||
    name.endsWith(".zip") ||
    name.endsWith(".rar") ||
    name.endsWith(".7z")
  ) {
    return FileArchive;
  }

  if (
    name.endsWith(".js") ||
    name.endsWith(".ts") ||
    name.endsWith(".vue") ||
    name.endsWith(".py") ||
    name.endsWith(".html") ||
    name.endsWith(".css") ||
    name.endsWith(".json")
  ) {
    return FileCode;
  }

  return FileIcon;
}

function onAttachmentRealtime(event) {
  const issueId = Number(event.detail?.issue_id);
  if (issueId === Number(props.issue.id)) {
    loadAttachments();
  }
}

function toDatetimeLocal(value) {
  if (!value) return "";

  const date = new Date(value);
  const offset = date.getTimezoneOffset();

  const localDate = new Date(date.getTime() - offset * 60 * 1000);

  return localDate.toISOString().slice(0, 16);
}

function fromDatetimeLocal(value) {
  if (!value) return null;

  return new Date(value).toISOString();
}

const checklistTotal = computed(() => checklists.value.length);

const checklistDone = computed(() => {
  return checklists.value.filter((item) => item.is_done).length;
});

const checklistPercent = computed(() => {
  if (checklistTotal.value === 0) return 0;
  return Math.round((checklistDone.value * 100) / checklistTotal.value);
});

onMounted(async () => {
  await Promise.all([loadComments(), loadAttachments(), loadChecklists()]);

  window.addEventListener("jira-attachment-refresh", onAttachmentRealtime);
  window.addEventListener("jira-checklist-refresh", onChecklistRealtime);
});

onBeforeUnmount(() => {
  window.removeEventListener("jira-attachment-refresh", onAttachmentRealtime);
  window.removeEventListener("jira-checklist-refresh", onChecklistRealtime);
});
</script>

<template>
  <ModalShell
    :title="issue.code"
    :subtitle="`Assigned to ${assigneeName}`"
    wide
    @close="emit('close')"
  >
    <div class="grid gap-6 lg:grid-cols-[1fr_320px]">
      <div class="space-y-4">
        <div>
          <label class="label">Title</label>
          <input v-model="form.title" class="input text-base font-bold" />
        </div>

        <div>
          <label class="label">Description</label>
          <textarea
            v-model="form.description"
            class="input min-h-44 resize-none"
          ></textarea>
        </div>

        <p
          v-if="error"
          class="rounded-xl bg-rose-50 px-4 py-3 text-sm font-medium text-rose-700"
        >
          {{ error }}
        </p>

        <div class="flex flex-wrap gap-3">
          <button class="btn-primary" :disabled="loading" @click="saveIssue">
            <Save class="h-4 w-4" />
            {{ loading ? "Saving..." : "Save changes" }}
          </button>
          <button class="btn-danger" :disabled="deleting" @click="deleteIssue">
            <Trash2 class="h-4 w-4" />
            {{ deleting ? "Deleting..." : "Delete" }}
          </button>
        </div>

        <section class="rounded-2xl border border-slate-200 bg-slate-50 p-4">
          <div class="mb-4 flex items-center justify-between gap-3">
            <div class="flex items-center gap-2">
              <ListChecks class="h-5 w-5 text-slate-500" />
              <h3 class="font-black text-slate-950">Checklist</h3>
            </div>

            <span
              v-if="checklistTotal > 0"
              class="rounded-full bg-white px-3 py-1 text-xs font-black text-slate-600 shadow-sm"
            >
              {{ checklistDone }}/{{ checklistTotal }}
            </span>
          </div>

          <div v-if="checklistTotal > 0" class="mb-4">
            <div
              class="mb-2 flex items-center justify-between text-xs font-bold text-slate-500"
            >
              <span>Progress</span>
              <span>{{ checklistPercent }}%</span>
            </div>

            <div class="h-2 overflow-hidden rounded-full bg-slate-200">
              <div
                class="h-full rounded-full bg-slate-900 transition-all duration-300"
                :style="{ width: `${checklistPercent}%` }"
              ></div>
            </div>
          </div>

          <form class="mb-4 flex gap-2" @submit.prevent="createChecklist">
            <input
              v-model="newChecklistTitle"
              type="text"
              placeholder="Add checklist item..."
              class="min-w-0 flex-1 rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm font-semibold text-slate-700 outline-none transition focus:border-blue-400"
            />

            <button
              type="submit"
              class="rounded-2xl bg-slate-900 px-4 py-3 text-sm font-black text-white transition hover:bg-slate-800 disabled:opacity-60"
              :disabled="checklistSaving || !newChecklistTitle.trim()"
            >
              <Plus class="h-4 w-4" />
            </button>
          </form>

          <div
            v-if="checklistLoading"
            class="rounded-2xl bg-white p-4 text-sm text-slate-500"
          >
            Loading checklist...
          </div>

          <div v-else class="space-y-2">
            <div
              v-for="item in checklists"
              :key="item.id"
              class="rounded-2xl bg-white p-3 shadow-sm"
            >
              <div class="flex items-start gap-3">
                <button
                  type="button"
                  class="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full border transition"
                  :class="
                    item.is_done
                      ? 'border-emerald-500 bg-emerald-500 text-white'
                      : 'border-slate-300 text-slate-400 hover:border-slate-500'
                  "
                  @click="toggleChecklist(item)"
                >
                  <Check v-if="item.is_done" class="h-4 w-4" />

                  <Circle v-else class="h-3 w-3" />
                </button>

                <div class="min-w-0 flex-1">
                  <div v-if="editingChecklistId === item.id" class="flex gap-2">
                    <input
                      v-model="editingChecklistTitle"
                      type="text"
                      class="min-w-0 flex-1 rounded-xl border border-slate-200 px-3 py-2 text-sm font-semibold outline-none focus:border-blue-400"
                      @keyup.enter="saveEditChecklist(item)"
                      @keyup.esc="cancelEditChecklist"
                    />

                    <button
                      type="button"
                      class="rounded-xl bg-slate-900 px-3 py-2 text-xs font-black text-white"
                      @click="saveEditChecklist(item)"
                    >
                      Save
                    </button>

                    <button
                      type="button"
                      class="rounded-xl border border-slate-200 px-3 py-2 text-xs font-black text-slate-500"
                      @click="cancelEditChecklist"
                    >
                      Cancel
                    </button>
                  </div>

                  <p
                    v-else
                    class="text-sm font-bold text-slate-800"
                    :class="item.is_done ? 'text-slate-400 line-through' : ''"
                  >
                    {{ item.title }}
                  </p>
                </div>

                <div
                  v-if="editingChecklistId !== item.id"
                  class="flex shrink-0 items-center gap-1"
                >
                  <button
                    type="button"
                    class="rounded-xl p-2 text-slate-400 hover:bg-slate-100 hover:text-slate-900"
                    title="Edit"
                    @click="startEditChecklist(item)"
                  >
                    <Pencil class="h-4 w-4" />
                  </button>

                  <button
                    type="button"
                    class="rounded-xl p-2 text-rose-400 hover:bg-rose-50 hover:text-rose-600"
                    title="Delete"
                    @click="deleteChecklist(item)"
                  >
                    <Trash2 class="h-4 w-4" />
                  </button>
                </div>
              </div>
            </div>

            <p
              v-if="checklists.length === 0"
              class="rounded-2xl bg-white p-4 text-sm text-slate-500"
            >
              No checklist items yet.
            </p>
          </div>
        </section>

        <section class="rounded-2xl border border-slate-200 bg-slate-50 p-4">
          <div class="mb-4 flex items-center justify-between gap-3">
            <div class="flex items-center gap-2">
              <Paperclip class="h-5 w-5 text-slate-500" />
              <h3 class="font-black text-slate-950">Attachments</h3>
            </div>

            <div>
              <input
                ref="attachmentInput"
                type="file"
                multiple
                class="hidden"
                @change="uploadAttachment"
              />

              <button
                type="button"
                class="btn-secondary"
                :disabled="uploadingAttachment"
                @click="attachmentInput?.click()"
              >
                <Upload class="h-4 w-4" />
                {{ uploadingAttachment ? "Uploading..." : "Upload files" }}
              </button>
            </div>
          </div>

          <div
            class="mb-4 rounded-2xl border-2 border-dashed p-6 text-center transition"
            :class="
              isDraggingFile
                ? 'border-blue-400 bg-blue-50'
                : 'border-slate-200 bg-white'
            "
            @dragover.prevent="isDraggingFile = true"
            @dragleave.prevent="isDraggingFile = false"
            @drop="handleFileDrop"
          >
            <Upload class="mx-auto mb-2 h-6 w-6 text-slate-400" />
            <p class="text-sm font-bold text-slate-700">
              Drag and drop files here
            </p>
            <p class="mt-1 text-xs text-slate-400">
              Maximum 10 files, each file less than 10MB
            </p>
          </div>

          <div
            v-if="uploadingAttachment"
            class="mb-4 rounded-2xl border border-blue-100 bg-blue-50 p-4"
          >
            <div class="mb-2 flex items-center justify-between gap-3">
              <div class="min-w-0">
                <p class="text-sm font-black text-blue-900">
                  Uploading {{ uploadingFileNames.length }} file(s)...
                </p>

                <p class="mt-1 truncate text-xs text-blue-700">
                  {{ uploadingFileNames.join(", ") }}
                </p>
              </div>

              <span class="text-sm font-black text-blue-700">
                {{ uploadProgress }}%
              </span>
            </div>

            <div class="h-2 overflow-hidden rounded-full bg-blue-100">
              <div
                class="h-full rounded-full bg-blue-600 transition-all duration-300"
                :style="{ width: `${uploadProgress}%` }"
              ></div>
            </div>
          </div>

          <div
            v-if="attachmentLoading"
            class="rounded-2xl bg-white p-4 text-sm text-slate-500"
          >
            Loading attachments...
          </div>

          <div v-else class="space-y-3">
            <div
              v-for="attachment in attachments"
              :key="attachment.id"
              class="flex items-center justify-between gap-3 rounded-2xl bg-white p-4 shadow-sm"
            >
              <div class="flex min-w-0 items-center gap-3">
                <div
                  class="flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl bg-slate-100 text-slate-500"
                >
                  <component
                    :is="getAttachmentIcon(attachment)"
                    class="h-5 w-5"
                  />
                </div>

                <div class="min-w-0">
                  <p class="truncate text-sm font-black text-slate-900">
                    {{ attachment.original_name }}
                  </p>

                  <p class="mt-1 text-xs text-slate-400">
                    {{ formatFileSize(attachment.size_bytes) }}
                    ·
                    {{ new Date(attachment.created_at).toLocaleString() }}
                  </p>
                </div>
              </div>

              <div class="flex shrink-0 items-center gap-2">
                <button
                  v-if="canPreview(attachment)"
                  type="button"
                  class="rounded-xl border border-slate-200 p-2 text-slate-500 hover:bg-slate-100 hover:text-slate-900"
                  title="Preview"
                  @click="previewAttachment(attachment)"
                >
                  <Eye class="h-4 w-4" />
                </button>

                <button
                  type="button"
                  class="rounded-xl border border-slate-200 p-2 text-slate-500 hover:bg-slate-100 hover:text-slate-900"
                  title="Download"
                  @click="downloadAttachment(attachment)"
                >
                  <Download class="h-4 w-4" />
                </button>

                <button
                  type="button"
                  class="rounded-xl border border-rose-200 p-2 text-rose-500 hover:bg-rose-50"
                  title="Delete"
                  @click="deleteAttachment(attachment)"
                >
                  <X class="h-4 w-4" />
                </button>
              </div>
            </div>

            <p
              v-if="attachments.length === 0"
              class="rounded-2xl bg-white p-4 text-sm text-slate-500"
            >
              No attachments yet.
            </p>
          </div>
        </section>

        <section class="rounded-2xl border border-slate-200 bg-slate-50 p-4">
          <div class="mb-4 flex items-center gap-2">
            <MessageCircle class="h-5 w-5 text-slate-500" />
            <h3 class="font-black text-slate-950">Comments</h3>
          </div>

          <form class="mb-4 flex gap-2" @submit.prevent="addComment">
            <input
              v-model="commentText"
              class="input"
              placeholder="Write a comment..."
            />
            <button
              class="btn-primary whitespace-nowrap"
              :disabled="commentLoading"
            >
              Send
            </button>
          </form>

          <div class="space-y-3">
            <div
              v-for="comment in comments"
              :key="comment.id"
              class="rounded-2xl bg-white p-4 shadow-sm"
            >
              <div class="mb-1 flex items-center justify-between gap-2">
                <p class="text-sm font-black text-slate-900">
                  {{ comment.author.full_name }}
                </p>
                <p class="text-xs text-slate-400">
                  {{ new Date(comment.created_at).toLocaleString() }}
                </p>
              </div>
              <p class="text-sm leading-6 text-slate-600">{{ comment.body }}</p>
            </div>
            <p
              v-if="comments.length === 0"
              class="rounded-2xl bg-white p-4 text-sm text-slate-500"
            >
              No comments yet.
            </p>
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
            <option
              v-for="member in members"
              :key="member.user_id"
              :value="member.user_id"
            >
              {{ member.user.full_name }}
            </option>
          </select>
        </div>
        <div>
          <label class="mb-2 block text-sm font-bold text-slate-600">
            Due date
          </label>

          <input
            v-model="form.due_date"
            type="datetime-local"
            class="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm font-semibold text-slate-700 outline-none transition focus:border-blue-400"
          />

          <p
            v-if="props.issue.is_overdue"
            class="mt-2 text-xs font-bold text-rose-600"
          >
            This task is overdue
          </p>
        </div>
        <div class="rounded-2xl bg-slate-50 p-4 text-sm text-slate-600">
          <p><b>Reporter ID:</b> {{ issue.reporter_id || currentUser?.id }}</p>
          <p>
            <b>Created:</b>
            {{ new Date(issue.created_at).toLocaleDateString() }}
          </p>
          <p>
            <b>Updated:</b>
            {{ new Date(issue.updated_at).toLocaleDateString() }}
          </p>
        </div>
      </aside>
    </div>
  </ModalShell>
</template>
