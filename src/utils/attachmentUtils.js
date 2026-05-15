export function canPreviewAttachment(attachment) {
  const type = attachment?.content_type || "";

  return (
    type.startsWith("image/") ||
    type === "application/pdf" ||
    type.startsWith("text/")
  );
}

export function formatFileSize(bytes) {
  if (!bytes) return "0 B";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}
