export const ACTIVITY_LABELS = {
  ISSUE_CREATED: "Created issue",
  ISSUE_UPDATED: "Updated issue",
  ISSUE_MOVED: "Moved issue",
  CHECKLIST_CREATED: "Added checklist",
  CHECKLIST_UPDATED: "Updated checklist",
  CHECKLIST_DELETED: "Deleted checklist",
  LABEL_CREATED: "Created label",
  LABEL_UPDATED: "Updated label",
  LABEL_DELETED: "Deleted label",
  ISSUE_LABEL_ADDED: "Added label",
  ISSUE_LABEL_REMOVED: "Removed label",
  COMMENT_CREATED: "Commented",
  ATTACHMENT_UPLOADED: "Uploaded file",
  EPIC_CREATED: "Created epic",
  EPIC_UPDATED: "Updated epic",
  EPIC_DELETED: "Deleted epic",
  SPRINT_CREATED: "Created sprint",
  SPRINT_UPDATED: "Updated sprint",
  SPRINT_DELETED: "Deleted sprint",
  ISSUE_EPIC_UPDATED: "Updated epic",
  ISSUE_SPRINT_UPDATED: "Updated sprint",
};

export const ACTIVITY_CLASSES = {
  ISSUE_CREATED: "bg-emerald-50 text-emerald-700 border-emerald-100",
  ISSUE_UPDATED: "bg-blue-50 text-blue-700 border-blue-100",
  ISSUE_MOVED: "bg-amber-50 text-amber-700 border-amber-100",
  CHECKLIST_CREATED: "bg-violet-50 text-violet-700 border-violet-100",
  CHECKLIST_UPDATED: "bg-violet-50 text-violet-700 border-violet-100",
  CHECKLIST_DELETED: "bg-rose-50 text-rose-700 border-rose-100",
  ISSUE_LABEL_ADDED: "bg-cyan-50 text-cyan-700 border-cyan-100",
  ISSUE_LABEL_REMOVED: "bg-orange-50 text-orange-700 border-orange-100",
  ATTACHMENT_UPLOADED: "bg-slate-50 text-slate-700 border-slate-100",
  EPIC_CREATED: "bg-violet-50 text-violet-700 border-violet-100",
  EPIC_UPDATED: "bg-violet-50 text-violet-700 border-violet-100",
  SPRINT_CREATED: "bg-blue-50 text-blue-700 border-blue-100",
  SPRINT_UPDATED: "bg-blue-50 text-blue-700 border-blue-100",
};

export function getActivityLabel(action) {
  return ACTIVITY_LABELS[action] || action || "Activity";
}

export function getActivityClass(action) {
  return ACTIVITY_CLASSES[action] || "bg-slate-50 text-slate-700 border-slate-100";
}

export function getChangedFields(log, excludedKeys = ["id", "code"]) {
  if (!log?.new_value) return "";

  const excluded = new Set(excludedKeys);
  const fields = Object.keys(log.new_value).filter((key) => !excluded.has(key));

  return fields.length ? fields.join(", ") : "";
}
