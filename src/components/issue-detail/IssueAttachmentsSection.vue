<script setup>
import { onBeforeUnmount, onMounted, ref } from "vue";
import {
  Download,
  Eye,
  File as FileIcon,
  FileArchive,
  FileCode,
  FileSpreadsheet,
  FileText,
  Image,
  Paperclip,
  Upload,
  X,
} from "lucide-vue-next";
import { attachmentApi, getErrorMessage } from "../../services/api";

const props = defineProps({
  issue: { type: Object, required: true },
  canEdit: { type: Boolean, default: true },
});

const attachments = ref([]);
const inputRef = ref(null);
const loading = ref(false);
const uploading = ref(false);
const dragging = ref(false);
const progress = ref(0);
const uploadingNames = ref([]);
const error = ref("");

async function loadAttachments() {
  loading.value = true;
  error.value = "";

  try {
    attachments.value = await attachmentApi.list(props.issue.id);
  } catch (err) {
    error.value = getErrorMessage(err);
  } finally {
    loading.value = false;
  }
}

async function uploadFiles(files) {
  const selectedFiles = Array.from(files || []);
  if (selectedFiles.length === 0) return;

  if (selectedFiles.length > 10) {
    error.value = "You can upload up to 10 files at once";
    return;
  }

  const oversizedFile = selectedFiles.find((file) => file.size > 10 * 1024 * 1024);
  if (oversizedFile) {
    error.value = `File "${oversizedFile.name}" must be less than 10MB`;
    return;
  }

  uploading.value = true;
  progress.value = 0;
  uploadingNames.value = selectedFiles.map((file) => file.name);
  error.value = "";

  try {
    const updateProgress = (percent) => {
      progress.value = percent;
    };

    if (selectedFiles.length === 1) {
      await attachmentApi.upload(props.issue.id, selectedFiles[0], updateProgress);
    } else {
      await attachmentApi.uploadMany(props.issue.id, selectedFiles, updateProgress);
    }

    progress.value = 100;
    await loadAttachments();
  } catch (err) {
    error.value = getErrorMessage(err);
  } finally {
    window.setTimeout(() => {
      uploading.value = false;
      progress.value = 0;
      uploadingNames.value = [];
    }, 600);
  }
}

async function uploadAttachment(event) {
  await uploadFiles(event.target.files);
  event.target.value = "";
}

async function handleDrop(event) {
  event.preventDefault();
  dragging.value = false;
  await uploadFiles(event.dataTransfer?.files);
}

function canPreview(attachment) {
  const type = attachment.content_type || "";
  return type.startsWith("image/") || type === "application/pdf" || type.startsWith("text/");
}

async function previewAttachment(attachment) {
  try {
    const blob = await attachmentApi.preview(props.issue.id, attachment.id);
    const url = window.URL.createObjectURL(blob);
    window.open(url, "_blank");
    window.setTimeout(() => window.URL.revokeObjectURL(url), 60 * 1000);
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
    attachments.value = attachments.value.filter((item) => item.id !== attachment.id);
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

  if (type.includes("spreadsheet") || name.endsWith(".xls") || name.endsWith(".xlsx") || name.endsWith(".csv")) {
    return FileSpreadsheet;
  }

  if (type.includes("zip") || type.includes("rar") || type.includes("7z") || name.endsWith(".zip") || name.endsWith(".rar") || name.endsWith(".7z")) {
    return FileArchive;
  }

  if ([".js", ".ts", ".vue", ".py", ".html", ".css", ".json"].some((ext) => name.endsWith(ext))) {
    return FileCode;
  }

  return FileIcon;
}

function onRealtime(event) {
  const issueId = Number(event.detail?.issue_id);
  if (issueId === Number(props.issue.id)) loadAttachments();
}

onMounted(() => {
  loadAttachments();
  window.addEventListener("jira-attachment-refresh", onRealtime);
});

onBeforeUnmount(() => {
  window.removeEventListener("jira-attachment-refresh", onRealtime);
});
</script>

<template>
  <section class="rounded-2xl border border-slate-200 bg-slate-50 p-4">
    <div class="mb-4 flex items-center justify-between gap-3">
      <div class="flex items-center gap-2">
        <Paperclip class="h-5 w-5 text-slate-500" />
        <h3 class="font-black text-slate-950">Attachments</h3>
      </div>

      <div>
        <input ref="inputRef" type="file" multiple class="hidden" @change="uploadAttachment" />

        <button
          v-if="canEdit"
          type="button"
          class="btn-secondary"
          :disabled="uploading"
          @click="inputRef?.click()"
        >
          <Upload class="h-4 w-4" />
          {{ uploading ? "Uploading..." : "Upload files" }}
        </button>
      </div>
    </div>

    <p v-if="error" class="mb-3 rounded-xl bg-rose-50 px-4 py-3 text-sm font-medium text-rose-700">
      {{ error }}
    </p>

    <div
      v-if="canEdit"
      class="mb-4 rounded-2xl border-2 border-dashed p-6 text-center transition"
      :class="dragging ? 'border-blue-400 bg-blue-50' : 'border-slate-200 bg-white'"
      @dragover.prevent="dragging = true"
      @dragleave.prevent="dragging = false"
      @drop="handleDrop"
    >
      <Upload class="mx-auto mb-2 h-6 w-6 text-slate-400" />
      <p class="text-sm font-bold text-slate-700">Drag and drop files here</p>
      <p class="mt-1 text-xs text-slate-400">Maximum 10 files, each file less than 10MB</p>
    </div>

    <div v-if="uploading" class="mb-4 rounded-2xl border border-blue-100 bg-blue-50 p-4">
      <div class="mb-2 flex items-center justify-between gap-3">
        <div class="min-w-0">
          <p class="text-sm font-black text-blue-900">
            Uploading {{ uploadingNames.length }} file(s)...
          </p>
          <p class="mt-1 truncate text-xs text-blue-700">{{ uploadingNames.join(", ") }}</p>
        </div>
        <span class="text-sm font-black text-blue-700">{{ progress }}%</span>
      </div>

      <div class="h-2 overflow-hidden rounded-full bg-blue-100">
        <div class="h-full rounded-full bg-blue-600 transition-all duration-300" :style="{ width: `${progress}%` }"></div>
      </div>
    </div>

    <div v-if="loading" class="rounded-2xl bg-white p-4 text-sm text-slate-500">
      Loading attachments...
    </div>

    <div v-else class="space-y-3">
      <div
        v-for="attachment in attachments"
        :key="attachment.id"
        class="flex items-center justify-between gap-3 rounded-2xl bg-white p-4 shadow-sm"
      >
        <div class="flex min-w-0 items-center gap-3">
          <div class="flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl bg-slate-100 text-slate-500">
            <component :is="getAttachmentIcon(attachment)" class="h-5 w-5" />
          </div>

          <div class="min-w-0">
            <p class="truncate text-sm font-black text-slate-900">{{ attachment.original_name }}</p>
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
            v-if="canEdit"
            type="button"
            class="rounded-xl border border-rose-200 p-2 text-rose-500 hover:bg-rose-50"
            title="Delete"
            @click="deleteAttachment(attachment)"
          >
            <X class="h-4 w-4" />
          </button>
        </div>
      </div>

      <p v-if="attachments.length === 0" class="rounded-2xl bg-white p-4 text-sm text-slate-500">
        No attachments yet.
      </p>
    </div>
  </section>
</template>
