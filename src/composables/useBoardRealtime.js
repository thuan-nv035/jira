import { ref } from "vue";
import { createProjectSocket } from "../services/socket";

export function useBoardRealtime({
  projectId,
  loadEpics,
  loadSprints,
  refreshIssues,
  loadProjectLabels,
  loadProjectLogs,
  loadProjectMembers,
  loadBoard,
  applyIssueMovedLocal,
}) {
  const socketStatus = ref("disconnected");
  const lastEvent = ref(null);
  let socket = null;

  function onSocketMessage(payload) {
    lastEvent.value = payload;

    if (["epic.created", "epic.updated", "epic.deleted"].includes(payload.event)) {
      loadEpics({ silent: true });
      refreshIssues({ silent: true });
      return;
    }

    if (["sprint.created", "sprint.updated", "sprint.deleted"].includes(payload.event)) {
      loadSprints({ silent: true });
      refreshIssues({ silent: true });
      return;
    }

    if (["issue.epic_updated", "issue.sprint_updated"].includes(payload.event)) {
      refreshIssues({ silent: true });
      window.dispatchEvent(new CustomEvent("jira-epic-sprint-refresh", { detail: payload.data }));
      return;
    }

    if (["label.created", "label.updated", "label.deleted"].includes(payload.event)) {
      loadProjectLabels({ silent: true });
      refreshIssues({ silent: true });
      window.dispatchEvent(new CustomEvent("jira-label-refresh", { detail: payload.data }));
      return;
    }

    if (["issue.label_added", "issue.label_removed"].includes(payload.event)) {
      window.dispatchEvent(new CustomEvent("jira-label-refresh", { detail: payload.data }));
      refreshIssues({ silent: true });
      return;
    }

    if (
      [
        "issue.created",
        "issue.updated",
        "issue.moved",
        "issue.deleted",
        "checklist.created",
        "checklist.updated",
        "checklist.deleted",
        "activity.created",
        "member.added",
      ].includes(payload.event)
    ) {
      window.dispatchEvent(new CustomEvent("jira-dashboard-refresh"));
    }

    if (["checklist.created", "checklist.updated", "checklist.deleted"].includes(payload.event)) {
      window.dispatchEvent(new CustomEvent("jira-checklist-refresh", { detail: payload.data }));
      refreshIssues({ silent: true });
      return;
    }

    if (payload.event === "activity.created") {
      loadProjectLogs({ reset: true, silent: true });
      window.dispatchEvent(new CustomEvent("jira-activity-refresh", { detail: payload.data }));
    }

    if (payload.event === "notification.created") {
      window.dispatchEvent(new CustomEvent("jira-notification-refresh", { detail: payload.data }));
    }

    if (["attachment.uploaded", "attachment.deleted"].includes(payload.event)) {
      window.dispatchEvent(new CustomEvent("jira-attachment-refresh", { detail: payload.data }));
    }

    if (payload.event === "issue.moved") {
      applyIssueMovedLocal(payload.data);
      return;
    }

    if (["member.role_updated", "member.removed"].includes(payload.event)) {
      loadProjectMembers();
      window.dispatchEvent(new CustomEvent("jira-dashboard-refresh"));
      return;
    }

    if (
      [
        "issue.created",
        "issue.updated",
        "issue.deleted",
        "comment.created",
        "attachment.uploaded",
        "attachment.deleted",
        "activity.created",
      ].includes(payload.event)
    ) {
      refreshIssues({ silent: true });
      return;
    }

    if (["column.created", "column.updated", "column.deleted", "member.added", "notification.created"].includes(payload.event)) {
      loadBoard({ silent: true });
    }
  }

  function connectRealtime() {
    socket = createProjectSocket(projectId.value, onSocketMessage, (status) => {
      socketStatus.value = status;
    });
  }

  function closeRealtime() {
    socket?.close();
  }

  return {
    socketStatus,
    lastEvent,
    onSocketMessage,
    connectRealtime,
    closeRealtime,
  };
}
