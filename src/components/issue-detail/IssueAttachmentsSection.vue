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
import { useIssueAttachments } from "../../composables/useIssueAttachments";
import { formatDateTime } from "../../utils/dateUtils";

const props = defineProps({
  issue: {
    type: Object,
    required: true,
  },
  canEdit: {
    type: Boolean,
    default: true,
  },
});

const error = ref("");

const {
  attachments,
  attachmentInput,
  attachmentLoading,
  uploadingAttachment,
  isDraggingFile,
  uploadProgress,
  uploadingFileNames,
  loadAttachments,
  uploadAttachment,
  handleFileDrop,
  canPreview,
  previewAttachment,
  downloadAttachment,
  deleteAttachment,
  formatFileSize,
  onAttachmentRealtime,
} = useIssueAttachments({
  props,
  error,
});

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

  if ([".js", ".ts", ".vue", ".py", ".html", ".css", ".json"].some((ext) => name.endsWith(ext))) {
    return FileCode;
  }

  return FileIcon;
}

onMounted(() => {
  loadAttachments();
  window.addEventListener("jira-attachment-refresh", onAttachmentRealtime);
});

onBeforeUnmount(() => {
  window.removeEventListener("jira-attachment-refresh", onAttachmentRealtime);
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
        <input
          ref="attachmentInput"
          type="file"
          multiple
          class="hidden"
          @change="uploadAttachment"
        />

        <button
          v-if="canEdit"
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

    <p
      v-if="error"
      class="mb-3 rounded-xl bg-rose-50 px-4 py-3 text-sm font-medium text-rose-700"
    >
      {{ error }}
    </p>

    <div
      v-if="canEdit"
      class="mb-4 rounded-2xl border-2 border-dashed p-6 text-center transition"
      :class="isDraggingFile ? 'border-blue-400 bg-blue-50' : 'border-slate-200 bg-white'"
      @dragover.prevent="isDraggingFile = true"
      @dragleave.prevent="isDraggingFile = false"
      @drop="handleFileDrop"
    >
      <Upload class="mx-auto mb-2 h-6 w-6 text-slate-400" />
      <p class="text-sm font-bold text-slate-700">Drag and drop files here</p>
      <p class="mt-1 text-xs text-slate-400">Maximum 10 files, each file less than 10MB</p>
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
          <div class="flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl bg-slate-100 text-slate-500">
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
              {{ formatDateTime(attachment.created_at) }}
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

      <p
        v-if="attachments.length === 0"
        class="rounded-2xl bg-white p-4 text-sm text-slate-500"
      >
        No attachments yet.
      </p>
    </div>
  </section>
</template>
