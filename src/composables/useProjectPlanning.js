import { reactive, ref } from "vue";
import { epicApi, getErrorMessage, sprintApi } from "../services/api";
import { useToast } from "./useToast";
export function useProjectPlanning({ projectId, error, refreshIssues, canEditIssues }) {
  const epics = ref([]);
  const sprints = ref([]);
  const epicLoading = ref(false);
  const sprintLoading = ref(false);
  const toast = useToast();
  const epicForm = reactive({ name: "", description: "", color: "#7c3aed" });
  const sprintForm = reactive({ name: "", goal: "", start_date: "", end_date: "", status: "PLANNED" });

  async function loadEpics(options = {}) {
    const silent = options.silent ?? false;
    if (!projectId.value) return;
    if (!silent) epicLoading.value = true;

    try {
      epics.value = await epicApi.list(projectId.value);
    } catch (err) {
      error.value = getErrorMessage(err);
    } finally {
      epicLoading.value = false;
    }
  }

  async function loadSprints(options = {}) {
    const silent = options.silent ?? false;
    if (!projectId.value) return;
    if (!silent) sprintLoading.value = true;

    try {
      sprints.value = await sprintApi.list(projectId.value);
    } catch (err) {
      error.value = getErrorMessage(err);
    } finally {
      sprintLoading.value = false;
    }
  }

  async function createEpic() {
    const name = epicForm.name.trim();
    if (!name) return;

    try {
      await epicApi.create(projectId.value, {
        name,
        description: epicForm.description || null,
        color: epicForm.color || "#7c3aed",
      });
      epicForm.name = "";
      epicForm.description = "";
      epicForm.color = "#7c3aed";
      await loadEpics({ silent: true });
    } catch (err) {
      error.value = getErrorMessage(err);
      toast.error(error.value);
    }
  }

  async function createSprint() {
    const name = sprintForm.name.trim();
    if (!name) return;

    try {
      await sprintApi.create(projectId.value, {
        name,
        goal: sprintForm.goal || null,
        start_date: sprintForm.start_date ? new Date(sprintForm.start_date).toISOString() : null,
        end_date: sprintForm.end_date ? new Date(sprintForm.end_date).toISOString() : null,
        status: sprintForm.status || "PLANNED",
      });
      sprintForm.name = "";
      sprintForm.goal = "";
      sprintForm.start_date = "";
      sprintForm.end_date = "";
      sprintForm.status = "PLANNED";
      await loadSprints({ silent: true });
    } catch (err) {
      error.value = getErrorMessage(err);
      toast.error(error.value);
    }
  }

  async function deleteEpic(epic) {
    if (!canEditIssues.value) return;
    if (!confirm(`Delete epic "${epic.name}"?`)) return;

    try {
      await epicApi.remove(epic.id);
      epics.value = epics.value.filter((item) => item.id !== epic.id);
      await refreshIssues({ silent: true });
    } catch (err) {
      error.value = getErrorMessage(err);
      toast.error(error.value);
    }
  }

  async function deleteSprint(sprint) {
    if (!canEditIssues.value) return;
    if (!confirm(`Delete sprint "${sprint.name}"?`)) return;

    try {
      await sprintApi.remove(sprint.id);
      sprints.value = sprints.value.filter((item) => item.id !== sprint.id);
      await refreshIssues({ silent: true });
    } catch (err) {
      error.value = getErrorMessage(err);
      toast.error(error.value);
    }
  }

  return {
    epics,
    sprints,
    epicLoading,
    sprintLoading,
    epicForm,
    sprintForm,
    loadEpics,
    loadSprints,
    createEpic,
    createSprint,
    deleteEpic,
    deleteSprint,
  };
}
