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
  const checklistDone = computed(() => checklists.value.filter((item) => item.is_done).length);
  const checklistPercent = computed(() => {
    if (checklistTotal.value === 0) return 0;
    return Math.round((checklistDone.value * 100) / checklistTotal.value);
  });

  async function loadChecklists() {
    checklistLoading.value = true;

    try {
      checklists.value = await checklistApi.list(props.issue.id);
    } catch (err) {
      error.value = getErrorMessage(err);
    } finally {
      checklistLoading.value = false;
    }
  }

  async function createChecklist() {
    const title = newChecklistTitle.value.trim();
    if (!title) return;

    checklistSaving.value = true;
    error.value = "";

    try {
      await checklistApi.create(props.issue.id, { title });
      newChecklistTitle.value = "";
      await loadChecklists();
    } catch (err) {
      error.value = getErrorMessage(err);
      toast.error(error.value);
    } finally {
      checklistSaving.value = false;
    }
  }

  async function toggleChecklist(item) {
    try {
      const nextValue = !item.is_done;
      item.is_done = nextValue;
      await checklistApi.update(item.id, { is_done: nextValue });
      await loadChecklists();
    } catch (err) {
      item.is_done = !item.is_done;
      error.value = getErrorMessage(err);
      toast.error(error.value);
    }
  }

  function startEditChecklist(item) {
    editingChecklistId.value = item.id;
    editingChecklistTitle.value = item.title;
  }

  function cancelEditChecklist() {
    editingChecklistId.value = null;
    editingChecklistTitle.value = "";
  }

  async function saveEditChecklist(item) {
    const title = editingChecklistTitle.value.trim();

    if (!title) {
      error.value = "Checklist title is required";
      return;
    }

    try {
      await checklistApi.update(item.id, { title });
      editingChecklistId.value = null;
      editingChecklistTitle.value = "";
      await loadChecklists();
    } catch (err) {
      error.value = getErrorMessage(err);
      toast.error(error.value);
    }
  }

  async function deleteChecklist(item) {
    if (!confirm(`Delete checklist "${item.title}"?`)) return;

    try {
      await checklistApi.remove(item.id);
      checklists.value = checklists.value.filter((checklist) => checklist.id !== item.id);
    } catch (err) {
      error.value = getErrorMessage(err);
      toast.error(error.value);
    }
  }

  function onChecklistRealtime(event) {
    const issueId = Number(event.detail?.issue_id);
    if (issueId === Number(props.issue.id)) loadChecklists();
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
    onChecklistRealtime,
  };
}
