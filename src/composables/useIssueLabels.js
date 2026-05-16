import { computed, ref } from "vue";
import { getErrorMessage, labelApi } from "../services/api";
import { useToast } from "./useToast";

export function useIssueLabels({ props, error }) {
  const issueLabels = ref([]);
  const labelLoading = ref(false);

  const toast = useToast();

  const availableLabels = computed(() => {
    const selectedIds = new Set(
      issueLabels.value.map((label) => Number(label.id))
    );

    return props.projectLabels.filter(
      (label) => !selectedIds.has(Number(label.id))
    );
  });

  function setError(err) {
    const message = getErrorMessage(err);
    error.value = message;
    toast.error(message);
  }

  async function loadIssueLabels(options = {}) {
    const silent = options.silent ?? false;

    if (!props.issue?.id) return;

    if (!silent) {
      labelLoading.value = true;
    }

    try {
      issueLabels.value = await labelApi.listIssueLabels(props.issue.id);
    } catch (err) {
      setError(err);
    } finally {
      labelLoading.value = false;
    }
  }

  async function addLabelToIssue(labelId) {
    if (!labelId || !props.canEdit) return;

    try {
      issueLabels.value = await labelApi.addToIssue(
        props.issue.id,
        Number(labelId)
      );

      toast.success("Label added");
    } catch (err) {
      setError(err);
    }
  }

  async function removeLabelFromIssue(label) {
    if (!label || !props.canEdit) return;

    try {
      await labelApi.removeFromIssue(props.issue.id, label.id);

      issueLabels.value = issueLabels.value.filter(
        (item) => Number(item.id) !== Number(label.id)
      );

      toast.success("Label removed");
    } catch (err) {
      setError(err);
    }
  }

  function onLabelRealtime(event) {
    const issueId = Number(event.detail?.issue_id);

    if (!issueId || issueId === Number(props.issue.id)) {
      loadIssueLabels({ silent: true });
    }
  }

  return {
    issueLabels,
    labelLoading,
    availableLabels,
    loadIssueLabels,
    addLabelToIssue,
    removeLabelFromIssue,
    onLabelRealtime,
  };
}
