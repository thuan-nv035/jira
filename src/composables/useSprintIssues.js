import { backlogApi, getErrorMessage } from "../services/api";

export function useSprintIssues({ projectId, sprintId, issues, error }) {
  async function refreshIssues(options = {}) {
    if (!projectId.value || !sprintId.value) return;

    try {
      issues.value = await backlogApi.listSprintIssues(
        projectId.value,
        sprintId.value,
        { limit: 200, offset: 0 },
      );
    } catch (err) {
      if (!(options.silent ?? false)) {
        error.value = getErrorMessage(err);
      }
    }
  }

  return { refreshIssues };
}
