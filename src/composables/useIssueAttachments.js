import { ref } from "vue";
import { attachmentApi, getErrorMessage } from "../services/api";
import { canPreviewAttachment, formatFileSize } from "../utils/attachmentUtils";

export function useIssueAttachments({ props, error }) {
  const attachments = ref([]);
  const attachmentInput = ref(null);
  const attachmentLoading = ref(false);
  const uploadingAttachment = ref(false);
  const isDraggingFile = ref(false);
  const uploadProgress = ref(0);
  const uploadingFileNames = ref([]);

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

    const oversizedFile = selectedFiles.find((file) => file.size > 10 * 1024 * 1024);
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
        await attachmentApi.upload(props.issue.id, selectedFiles[0], updateProgress);
      } else {
        await attachmentApi.uploadMany(props.issue.id, selectedFiles, updateProgress);
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
    await uploadFiles(event.dataTransfer?.files);
  }

  async function previewAttachment(attachment) {
    try {
      const blob = await attachmentApi.preview(props.issue.id, attachment.id);
      const url = window.URL.createObjectURL(blob);
      window.open(url, "_blank");
      setTimeout(() => window.URL.revokeObjectURL(url), 60 * 1000);
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

  function onAttachmentRealtime(event) {
    const issueId = Number(event.detail?.issue_id);
    if (issueId === Number(props.issue.id)) loadAttachments();
  }

  return {
    attachments,
    attachmentInput,
    attachmentLoading,
    uploadingAttachment,
    isDraggingFile,
    uploadProgress,
    uploadingFileNames,
    loadAttachments,
    uploadFiles,
    uploadAttachment,
    handleFileDrop,
    canPreview: canPreviewAttachment,
    previewAttachment,
    downloadAttachment,
    deleteAttachment,
    formatFileSize,
    onAttachmentRealtime,
  };
}
