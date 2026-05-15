import { computed, reactive, ref } from "vue";
import { getErrorMessage, issueApi } from "../services/api";
import { fromDatetimeLocal, toDatetimeLocal } from "../utils/dateUtils";
import { normalizeMember } from "../utils/memberUtils";
import { useToast } from "./useToast";
export function useIssueForm({ props, emit, error }) {
  const loading = ref(false);
  const deleting = ref(false);
  const toast = useToast();
  const form = reactive({
    title: props.issue.title,
    description: props.issue.description || "",
    issue_type: props.issue.issue_type,
    priority: props.issue.priority,
    assignee_id: props.issue.assignee_id || "",
    epic_id: props.issue.epic_id || "",
    sprint_id: props.issue.sprint_id || "",
    due_date: toDatetimeLocal(props.issue.due_date),
  });

  const assigneeName = computed(() => {
    const member = props.members.find((item) => item.user_id === props.issue.assignee_id);
    return member?.user?.full_name || "Unassigned";
  });

  const reporter = computed(() => {
    if (!props.issue.reporter_id) return null;

    return props.members
      .map(normalizeMember)
      .find((member) => Number(member.id) === Number(props.issue.reporter_id));
  });

  async function saveIssue() {
    loading.value = true;
    error.value = "";

    try {
      const updated = await issueApi.update(props.issue.project_id, props.issue.id, {
        title: form.title,
        description: form.description,
        issue_type: form.issue_type,
        priority: form.priority,
        assignee_id: form.assignee_id || null,
        due_date: fromDatetimeLocal(form.due_date),
      });

      emit("changed", updated);
    } catch (err) {
      error.value = getErrorMessage(err);
      toast.error(error.value);
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
      toast.error(error.value);
    } finally {
      deleting.value = false;
    }
  }

  return {
    loading,
    deleting,
    form,
    assigneeName,
    reporter,
    saveIssue,
    deleteIssue,
  };
}
