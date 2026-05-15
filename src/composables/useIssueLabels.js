import { computed, ref } from "vue";
import { getErrorMessage, labelApi } from "../services/api";
import { useToast } from "./useToast";
export function useIssueLabels({ props, error }) {
  const issueLabels = ref([]);
  const labelLoading = ref(false);
  const toast = useToast();
  const availableLabels = computed(() => {
    const selectedIds = new Set(issueLabels.value.map((label) => Number(label.id)));
    return props.projectLabels.filter((label) => !selectedIds.has(Number(label.id)));
  });

  async function loadIssueLabels() {
    labelLoading.value = true;

    try {
      issueLabels.value = await labelApi.listIssueLabels(props.issue.id);
    } catch (err) {
      error.value = getErrorMessage(err);
    } finally {
      labelLoading.value = false;
    }
  }

  async function addLabelToIssue(labelId) {
    if (!labelId || !props.canEdit) return;

    try {
      issueLabels.value = await labelApi.addToIssue(props.issue.id, labelId);
    } catch (err) {
      error.value = getErrorMessage(err);
      toast.error(error.value);
    }
  }

  async function removeLabelFromIssue(label) {
    if (!props.canEdit) return;

    try {
      await labelApi.removeFromIssue(props.issue.id, label.id);
      issueLabels.value = issueLabels.value.filter((item) => Number(item.id) !== Number(label.id));
    } catch (err) {
      error.value = getErrorMessage(err);
      toast.error(error.value);
    }
  }

  function onLabelRealtime(event) {
    const issueId = Number(event.detail?.issue_id);
    if (!issueId || issueId === Number(props.issue.id)) loadIssueLabels();
  }

  return { issueLabels, labelLoading, availableLabels, loadIssueLabels, addLabelToIssue, removeLabelFromIssue, onLabelRealtime };
}
