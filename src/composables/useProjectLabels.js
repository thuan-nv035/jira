import { reactive, ref } from "vue";
import { getErrorMessage, labelApi } from "../services/api";
import { useToast } from "./useToast";
export function useProjectLabels({ projectId, error, refreshIssues, canManageColumns }) {
  const projectLabels = ref([]);
  const labelLoading = ref(false);
  const labelForm = reactive({ name: "", color: "#2563eb" });
  const toast = useToast();
  async function loadProjectLabels(options = {}) {
    const silent = options.silent ?? false;
    if (!projectId.value) return;

    if (!silent) labelLoading.value = true;

    try {
      projectLabels.value = await labelApi.listProjectLabels(projectId.value);
    } catch (err) {
      error.value = getErrorMessage(err);
    } finally {
      labelLoading.value = false;
    }
  }

  async function createProjectLabel() {
    const name = labelForm.name.trim();
    if (!name) return;

    try {
      await labelApi.create(projectId.value, { name, color: labelForm.color || "#2563eb" });
      labelForm.name = "";
      labelForm.color = "#2563eb";
      await loadProjectLabels({ silent: true });
    } catch (err) {
      error.value = getErrorMessage(err);
      toast.error(error.value);
    }
  }

  async function deleteProjectLabel(label) {
    if (!canManageColumns.value) return;
    if (!confirm(`Delete label "${label.name}"?`)) return;

    try {
      await labelApi.remove(label.id);
      projectLabels.value = projectLabels.value.filter((item) => item.id !== label.id);
      await refreshIssues({ silent: true });
    } catch (err) {
      error.value = getErrorMessage(err);
      toast.error(error.value);
    }
  }

  return { projectLabels, labelLoading, labelForm, loadProjectLabels, createProjectLabel, deleteProjectLabel };
}
