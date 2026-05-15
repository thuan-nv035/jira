import { computed } from "vue";
import { epicApi, getErrorMessage, sprintApi } from "../services/api";
import { useToast } from "./useToast";
export function useIssuePlanning({ props, form, error, loadIssueActivities }) {
  const toast = useToast();
  const selectedEpic = computed(() => {
    if (!form.epic_id) return null;
    return props.epics.find((epic) => Number(epic.id) === Number(form.epic_id));
  });

  const selectedSprint = computed(() => {
    if (!form.sprint_id) return null;
    return props.sprints.find((sprint) => Number(sprint.id) === Number(form.sprint_id));
  });

  async function updateIssueEpic() {
    if (!props.canEdit) return;

    try {
      await epicApi.updateIssueEpic(props.issue.id, form.epic_id ? Number(form.epic_id) : null);

      window.dispatchEvent(new CustomEvent("jira-epic-sprint-refresh", {
        detail: { issue_id: props.issue.id },
      }));
    } catch (err) {
      error.value = getErrorMessage(err);
    }
  }

  async function updateIssueSprint() {
    if (!props.canEdit) return;

    try {
      await sprintApi.updateIssueSprint(props.issue.id, form.sprint_id ? Number(form.sprint_id) : null);

      window.dispatchEvent(new CustomEvent("jira-epic-sprint-refresh", {
        detail: { issue_id: props.issue.id },
      }));
    } catch (err) {
      error.value = getErrorMessage(err);
      toast.error(error.value);
    }
  }

  function onEpicSprintRealtime(event) {
    const issueId = Number(event.detail?.issue_id);

    if (issueId === Number(props.issue.id)) {
      loadIssueActivities({ reset: true, silent: true });
    }
  }

  return {
    selectedEpic,
    selectedSprint,
    updateIssueEpic,
    updateIssueSprint,
    onEpicSprintRealtime,
  };
}
