import { computed, reactive, ref, watch } from "vue";
import { getErrorMessage, issueApi } from "../services/api";
import { useToast } from "./useToast";
export function useIssueFilters({ projectId, issues, error }) {
  const filterLoading = ref(false);
  const toast = useToast();
  const filters = reactive({
    keyword: "",
    column_id: "",
    priority: "",
    issue_type: "",
    has_attachment: "",
    overdue: "",
    label_id: "",
    sort_by: "updated_at",
    order: "desc",
  });

  let filterTimer = null;

  const hasActiveIssueFilters = computed(() => {
    return Boolean(
      filters.keyword ||
        filters.column_id ||
        filters.priority ||
        filters.issue_type ||
        filters.overdue ||
        filters.label_id ||
        filters.has_attachment,
    );
  });

  function buildIssueSearchParams() {
    return {
      keyword: filters.keyword.trim(),
      column_id: filters.column_id ? Number(filters.column_id) : "",
      priority: filters.priority,
      issue_type: filters.issue_type,
      has_attachment:
        filters.has_attachment === "" ? "" : filters.has_attachment === "true",
      sort_by: filters.sort_by,
      order: filters.order,
      label_id: filters.label_id ? Number(filters.label_id) : "",
      overdue: filters.overdue === "" ? "" : filters.overdue === "true",
    };
  }

  async function refreshIssues(options = {}) {
    const silent = options.silent ?? false;

    if (!projectId.value) return;

    if (!silent) {
      filterLoading.value = true;
    }

    try {
      if (hasActiveIssueFilters.value) {
        issues.value = await issueApi.search(projectId.value, buildIssueSearchParams());
      } else {
        issues.value = await issueApi.list(projectId.value);
      }
    } catch (err) {
      error.value = getErrorMessage(err);
      toast.error(error.value);
    } finally {
      if (!silent) {
        filterLoading.value = false;
      }
    }
  }

  watch(
    filters,
    () => {
      clearTimeout(filterTimer);

      filterTimer = setTimeout(() => {
        refreshIssues({ silent: false });
      }, 350);
    },
    { deep: true },
  );

  function clearIssueFilters() {
    filters.keyword = "";
    filters.column_id = "";
    filters.priority = "";
    filters.issue_type = "";
    filters.has_attachment = "";
    filters.sort_by = "updated_at";
    filters.order = "desc";
    filters.overdue = "";
    filters.label_id = "";
  }

  function cleanupIssueFilters() {
    clearTimeout(filterTimer);
  }

  return {
    filters,
    filterLoading,
    hasActiveIssueFilters,
    buildIssueSearchParams,
    refreshIssues,
    clearIssueFilters,
    cleanupIssueFilters,
  };
}
