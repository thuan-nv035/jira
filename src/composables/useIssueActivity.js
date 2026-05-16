import { ref } from "vue";
import { activityApi, getErrorMessage } from "../services/api";
import { getActivityClass, getActivityLabel, getChangedFields } from "../utils/activityUtils";
import { formatDateTime } from "../utils/dateUtils";
import { useToast } from "./useToast";

const ISSUE_ACTIVITY_LIMIT = 10;
const SCROLL_LOAD_OFFSET = 80;

export function useIssueActivity({ props, error }) {
  const issueActivities = ref([]);
  const issueActivityLoading = ref(false);
  const issueActivityLoadingMore = ref(false);
  const issueActivityHasMore = ref(true);

  const toast = useToast();

  function setError(err) {
    const message = getErrorMessage(err);
    error.value = message;
    toast.error(message);
  }

  function mergeUniqueActivities(currentItems, newItems) {
    const currentIds = new Set(currentItems.map((item) => item.id));

    return [
      ...currentItems,
      ...newItems.filter((item) => !currentIds.has(item.id)),
    ];
  }

  async function loadIssueActivities(options = {}) {
    const reset = options.reset ?? false;
    const silent = options.silent ?? false;

    if (!props.issue?.id) return;
    if (issueActivityLoading.value || issueActivityLoadingMore.value) return;
    if (!reset && !issueActivityHasMore.value) return;

    const offset = reset ? 0 : issueActivities.value.length;

    if (reset) {
      issueActivityHasMore.value = true;

      if (!silent) {
        issueActivityLoading.value = true;
      }
    } else {
      issueActivityLoadingMore.value = true;
    }

    try {
      const data = await activityApi.listIssueLog(props.issue.id, {
        limit: ISSUE_ACTIVITY_LIMIT,
        offset,
      });

      issueActivities.value = reset
        ? data
        : mergeUniqueActivities(issueActivities.value, data);

      issueActivityHasMore.value = data.length === ISSUE_ACTIVITY_LIMIT;
    } catch (err) {
      setError(err);
    } finally {
      issueActivityLoading.value = false;
      issueActivityLoadingMore.value = false;
    }
  }

  function onIssueActivityScroll(event) {
    const el = event.target;

    const nearBottom =
      el.scrollTop + el.clientHeight >= el.scrollHeight - SCROLL_LOAD_OFFSET;

    if (nearBottom) {
      loadIssueActivities({
        reset: false,
        silent: true,
      });
    }
  }

  function onIssueActivityRealtime(event) {
    const issueId = Number(event.detail?.issue_id);

    if (!issueId || issueId === Number(props.issue.id)) {
      loadIssueActivities({
        reset: true,
        silent: true,
      });
    }
  }

  return {
    issueActivities,
    issueActivityLoading,
    issueActivityLoadingMore,
    issueActivityHasMore,
    loadIssueActivities,
    onIssueActivityScroll,
    onIssueActivityRealtime,
    formatActivityTime: formatDateTime,
    getActivityLabel,
    getActivityClass,
    getChangedFields,
  };
}
