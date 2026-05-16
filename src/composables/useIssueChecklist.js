import { computed, ref } from "vue";
import { checklistApi, getErrorMessage } from "../services/api";
import { useToast } from "./useToast";

export function useIssueChecklist({ props, error }) {
  const checklists = ref([]);
  const checklistLoading = ref(false);
  const checklistSaving = ref(false);

  const newChecklistTitle = ref("");
  const editingChecklistId = ref(null);
  const editingChecklistTitle = ref("");

  const toast = useToast();

  const checklistTotal = computed(() => checklists.value.length);

  const checklistDone = computed(() => {
    return checklists.value.filter((item) => item.is_done).length;
  });

  const checklistPercent = computed(() => {
    if (checklistTotal.value === 0) return 0;

    return Math.round((checklistDone.value * 100) / checklistTotal.value);
  });

  function setError(err) {
    const message = getErrorMessage(err);

    error.value = message;
    toast.error(message);
  }

  function requireEditable() {
    if (props.canEdit) return true;

    toast.warning("You only have view permission for this issue.");
    return false;
  }

  async function loadChecklists() {
    if (!props.issue?.id) return;

    checklistLoading.value = true;

    try {
      checklists.value = await checklistApi.list(props.issue.id);
    } catch (err) {
      setError(err);
    } finally {
      checklistLoading.value = false;
    }
  }

  async function createChecklist() {
    if (!requireEditable()) return;

    const title = newChecklistTitle.value.trim();

    if (!title) return;

    checklistSaving.value = true;
    error.value = "";

    try {
      await checklistApi.create(props.issue.id, { title });

      newChecklistTitle.value = "";
      await loadChecklists();

      toast.success("Checklist item added");
    } catch (err) {
      setError(err);
    } finally {
      checklistSaving.value = false;
    }
  }

  async function toggleChecklist(item) {
    if (!requireEditable()) return;

    const previousValue = item.is_done;
    const nextValue = !previousValue;

    item.is_done = nextValue;

    try {
      await checklistApi.update(item.id, {
        is_done: nextValue
      });

      await loadChecklists();
    } catch (err) {
      item.is_done = previousValue;
      setError(err);
    }
  }

  function startEditChecklist(item) {
    if (!requireEditable()) return;

    editingChecklistId.value = item.id;
    editingChecklistTitle.value = item.title;
  }

  function cancelEditChecklist() {
    editingChecklistId.value = null;
    editingChecklistTitle.value = "";
  }

  async function saveEditChecklist(item) {
    if (!requireEditable()) return;

    const title = editingChecklistTitle.value.trim();

    if (!title) {
      error.value = "Checklist title is required";
      toast.warning(error.value);
      return;
    }

    try {
      await checklistApi.update(item.id, { title });

      cancelEditChecklist();
      await loadChecklists();

      toast.success("Checklist item updated");
    } catch (err) {
      setError(err);
    }
  }

  async function deleteChecklist(item) {
    if (!requireEditable()) return;

    if (!window.confirm(`Delete checklist "${item.title}"?`)) return;

    try {
      await checklistApi.remove(item.id);

      checklists.value = checklists.value.filter((checklist) => {
        return checklist.id !== item.id;
      });

      toast.success("Checklist item deleted");
    } catch (err) {
      setError(err);
    }
  }

  function onChecklistRealtime(event) {
    const issueId = Number(event.detail?.issue_id);

    if (issueId === Number(props.issue.id)) {
      loadChecklists();
    }
  }

  return {
    checklists,
    checklistLoading,
    checklistSaving,
    newChecklistTitle,
    editingChecklistId,
    editingChecklistTitle,
    checklistTotal,
    checklistDone,
    checklistPercent,
    loadChecklists,
    createChecklist,
    toggleChecklist,
    startEditChecklist,
    cancelEditChecklist,
    saveEditChecklist,
    deleteChecklist,
    onChecklistRealtime
  };
}
