import { ref } from "vue";
import { activityApi, getErrorMessage } from "../services/api";
import { formatDateTime } from "../utils/dateUtils";
import { getActivityClass, getActivityLabel, getChangedFields } from "../utils/activityUtils";
import { useToast } from "./useToast";
export function useProjectActivity({ projectId, error }) {
  const projectLogs = ref([]);
  const projectLogLoading = ref(false);
  const projectLogLoadingMore = ref(false);
  const projectLogHasMore = ref(true);
  const PROJECT_LOG_LIMIT = 20;
  const toast = useToast();
  async function loadProjectLogs(options = {}) {
    const reset = options.reset ?? false;
    const silent = options.silent ?? false;

    if (!projectId.value) return;
    if (projectLogLoading.value || projectLogLoadingMore.value) return;
    if (!reset && !projectLogHasMore.value) return;

    const offset = reset ? 0 : projectLogs.value.length;

    if (reset) {
      projectLogHasMore.value = true;
      if (!silent) projectLogLoading.value = true;
    } else {
      projectLogLoadingMore.value = true;
    }

    try {
      const data = await activityApi.listProjectLog(projectId.value, {
        limit: PROJECT_LOG_LIMIT,
        offset,
      });

      if (reset) {
        projectLogs.value = data;
      } else {
        const currentIds = new Set(projectLogs.value.map((item) => item.id));
        const newItems = data.filter((item) => !currentIds.has(item.id));
        projectLogs.value = [...projectLogs.value, ...newItems];
      }

      projectLogHasMore.value = data.length === PROJECT_LOG_LIMIT;
    } catch (err) {
      error.value = getErrorMessage(err);
      toast.error(error.value);
    } finally {
      projectLogLoading.value = false;
      projectLogLoadingMore.value = false;
    }
  }

  function onProjectLogScroll(event) {
    const el = event.target;
    const nearBottom = el.scrollTop + el.clientHeight >= el.scrollHeight - 80;

    if (nearBottom) {
      loadProjectLogs({ reset: false, silent: true });
    }
  }

  return {
    projectLogs,
    projectLogLoading,
    projectLogLoadingMore,
    projectLogHasMore,
    loadProjectLogs,
    onProjectLogScroll,
    formatLogTime: formatDateTime,
    getActivityLabel,
    getActivityClass,
    getChangedFields,
  };
}
