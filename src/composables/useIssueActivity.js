import { ref } from "vue";
import { activityApi, getErrorMessage } from "../services/api";
import { formatDateTime } from "../utils/dateUtils";
import { getActivityClass, getActivityLabel, getChangedFields } from "../utils/activityUtils";
import { useToast } from "./useToast";

export function useIssueActivity({ props, error }) {
  const issueActivities = ref([]);
  const issueActivityLoading = ref(false);
  const issueActivityLoadingMore = ref(false);
  const issueActivityHasMore = ref(true);
  const toast = useToast();
  const ISSUE_ACTIVITY_LIMIT = 10;

  async function loadIssueActivities(options = {}) {
    const reset = options.reset ?? false;
    const silent = options.silent ?? false;

    if (!props.issue?.id) return;
    if (issueActivityLoading.value || issueActivityLoadingMore.value) return;
    if (!reset && !issueActivityHasMore.value) return;

    const offset = reset ? 0 : issueActivities.value.length;

    if (reset) {
      issueActivityHasMore.value = true;
      if (!silent) issueActivityLoading.value = true;
    } else {
      issueActivityLoadingMore.value = true;
    }

    try {
      const data = await activityApi.listIssueLog(props.issue.id, {
        limit: ISSUE_ACTIVITY_LIMIT,
        offset,
      });

      if (reset) {
        issueActivities.value = data;
      } else {
        const currentIds = new Set(issueActivities.value.map((item) => item.id));
        const newItems = data.filter((item) => !currentIds.has(item.id));
        issueActivities.value = [...issueActivities.value, ...newItems];
      }

      issueActivityHasMore.value = data.length === ISSUE_ACTIVITY_LIMIT;
    } catch (err) {
      error.value = getErrorMessage(err);
      toast.error(error.value);
    } finally {
      issueActivityLoading.value = false;
      issueActivityLoadingMore.value = false;
    }
  }

  function onIssueActivityScroll(event) {
    const el = event.target;
    const nearBottom = el.scrollTop + el.clientHeight >= el.scrollHeight - 80;

    if (nearBottom) {
      loadIssueActivities({ reset: false, silent: true });
    }
  }

  function onIssueActivityRealtime(event) {
    const issueId = Number(event.detail?.issue_id);

    if (!issueId || issueId === Number(props.issue.id)) {
      loadIssueActivities({ reset: true, silent: true });
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
