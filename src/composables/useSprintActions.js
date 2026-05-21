import { getErrorMessage, sprintApi } from "../services/api";
import { useToast } from "./useToast";

export function useSprintActions({ error, onUpdated }) {
  const toast = useToast();

  async function startSprint(sprint) {
    if (!sprint) return;

    try {
      await sprintApi.start(sprint.id);
      await onUpdated?.();
      toast.success("Sprint started");
    } catch (err) {
      error.value = getErrorMessage(err);
      toast.error(error.value);
    }
  }

  async function completeSprint(sprint) {
    if (!sprint) return;
    if (!confirm(`Complete sprint "${sprint.name}"?`)) return;

    try {
      await sprintApi.complete(sprint.id);
      await onUpdated?.();
      toast.success("Sprint completed");
    } catch (err) {
      error.value = getErrorMessage(err);
      toast.error(error.value);
    }
  }

  return { startSprint, completeSprint };
}
