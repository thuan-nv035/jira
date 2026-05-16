import { ref } from "vue";
import { attachmentApi, getErrorMessage } from "../services/api";
import { canPreviewAttachment, formatFileSize } from "../utils/attachmentUtils";
import { useToast } from "./useToast";

const MAX_FILES_PER_UPLOAD = 10;
const MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024;

export function useIssueAttachments({ props, error }) {
  const attachments = ref([]);
  const attachmentInput = ref(null);
  const attachmentLoading = ref(false);
  const uploadingAttachment = ref(false);
  const isDraggingFile = ref(false);
  const uploadProgress = ref(0);
  const uploadingFileNames = ref([]);

  const toast = useToast();

  function setError(err) {
    const message = typeof err === "string" ? err : getErrorMessage(err);

    error.value = message;
    toast.error(message);

    return message;
  }

  function validateFiles(files) {
    const selectedFiles = Array.from(files || []);

    if (selectedFiles.length === 0) {
      return [];
    }

    if (selectedFiles.length > MAX_FILES_PER_UPLOAD) {
      setError(`You can upload up to ${MAX_FILES_PER_UPLOAD} files at once`);
      return [];
    }

    const oversizedFile = selectedFiles.find((file) => file.size > MAX_FILE_SIZE_BYTES);

    if (oversizedFile) {
      setError(`File "${oversizedFile.name}" must be less than 10MB`);
      return [];
    }

    return selectedFiles;
  }

  async function loadAttachments() {
    attachmentLoading.value = true;
    error.value = "";

    try {
      attachments.value = await attachmentApi.list(props.issue.id);
    } catch (err) {
      setError(err);
    } finally {
      attachmentLoading.value = false;
    }
  }

  async function uploadFiles(files) {
    if (!props.canEdit) return;

    const selectedFiles = validateFiles(files);

    if (selectedFiles.length === 0) return;

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
      toast.success("File uploaded successfully");
      await loadAttachments();
    } catch (err) {
      setError(err);
    } finally {
      window.setTimeout(() => {
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

      window.setTimeout(() => {
        window.URL.revokeObjectURL(url);
      }, 60 * 1000);
    } catch (err) {
      setError(err);
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
      setError(err);
    }
  }

  async function deleteAttachment(attachment) {
    if (!props.canEdit) return;

    if (!window.confirm(`Delete file "${attachment.original_name}"?`)) return;

    try {
      await attachmentApi.remove(props.issue.id, attachment.id);

      attachments.value = attachments.value.filter((item) => item.id !== attachment.id);
      toast.success("File deleted successfully");
    } catch (err) {
      setError(err);
    }
  }

  function onAttachmentRealtime(event) {
    const issueId = Number(event.detail?.issue_id);

    if (issueId === Number(props.issue.id)) {
      loadAttachments();
    }
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
