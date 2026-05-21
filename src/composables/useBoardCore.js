import {
    computed,
    ref
} from "vue";
import {
    columnApi,
    getErrorMessage,
    issueApi,
    projectApi
} from "../services/api";
export function useBoardCore({
    projectId,
    route,
    router,
    issues,
    error,
    refreshIssues
}) {
    const project = ref(null);
    const columns = ref([]);
    const loading = ref(true);
    const showIssueForm = ref(false);
    const selectedColumn = ref(null);
    const selectedIssue = ref(null);
    const draggedIssue = ref(null);
    const issueTotal = computed(() => issues.value.length);

    const doneTotal = computed(() => {
        const doneColumn = columns.value.find((col) =>
            col.name.toUpperCase().includes("DONE"),
        );

        if (!doneColumn) return 0;

        return issues.value.filter((issue) => issue.column_id === doneColumn.id).length;
    });

    function issuesByColumn(columnId) {
        return issues.value.filter((issue) => issue.column_id === columnId);
    }

    async function loadBoard(options = {}) {
        const silent = options.silent ?? false;

        if (!silent) {
            loading.value = true;
            error.value = "";
        }

        try {
            const [projectData, columnData] = await Promise.all([
                projectApi.get(projectId.value),
                columnApi.list(projectId.value),
            ]);

            project.value = projectData;
            columns.value = columnData;
            await refreshIssues({
                silent: true
            });
        } catch (err) {
            error.value = getErrorMessage(err);
        } finally {
            if (!silent) {
                loading.value = false;
            }
        }
    }

    function openCreateIssue(column) {
        selectedColumn.value = column;
        showIssueForm.value = true;
    }

    function onIssueCreated(issue) {
        showIssueForm.value = false;
        issues.value = [...issues.value, issue];
    }

    function onIssueChanged(updatedIssue) {
        selectedIssue.value = updatedIssue;
        issues.value = updateIssueInList(issues.value, updatedIssue);
    }

    function onIssueDeleted(issueId) {
        selectedIssue.value = null;
        issues.value = issues.value.filter((item) => item.id !== issueId);
    }

    function onDragIssue(issue) {
        draggedIssue.value = issue;
    }

    async function onDropIssue(column) {
        if (!draggedIssue.value || draggedIssue.value.column_id === column.id) return;

        const issue = draggedIssue.value;
        draggedIssue.value = null;

        const oldIssues = [...issues.value];
        const nextPosition = issuesByColumn(column.id).length;

        issues.value = issues.value.map((item) =>
            item.id === issue.id ? {
                ...item,
                column_id: column.id,
                position: nextPosition
            } :
            item,
        );

        try {
            const moved = await issueApi.move(projectId.value, issue.id, {
                column_id: column.id,
                position: nextPosition,
            });

            issues.value = updateIssueInList(issues.value, moved);
        } catch (err) {
            issues.value = oldIssues;
            error.value = getErrorMessage(err);
        }
    }

    function applyIssueMovedLocal(data) {
        const issueId = Number(data.issue_id);
        const newColumnId = Number(data.column_id);
        const newPosition = Number(data.position ?? 0);
        const index = issues.value.findIndex((issue) => Number(issue.id) === issueId);

        if (index === -1) {
            loadBoard({
                silent: true
            });
            return;
        }

        issues.value[index] = {
            ...issues.value[index],
            column_id: newColumnId,
            position: newPosition,
        };

        issues.value = [...issues.value].sort((a, b) => {
            if (a.column_id !== b.column_id) return a.column_id - b.column_id;
            return a.position - b.position;
        });
    }

    async function openIssueFromQuery() {
        const issueId = Number(route.query.issueId);
        if (!issueId) return;

        let issue = issues.value.find((item) => Number(item.id) === issueId);

        if (!issue) {
            try {
                issue = await issueApi.get(projectId.value, issueId);
            } catch (err) {
                error.value = getErrorMessage(err);
                return;
            }
        }

        if (issue) selectedIssue.value = issue;
    }

    function closeIssueModal() {
        selectedIssue.value = null;

        const query = {
            ...route.query
        };
        delete query.issueId;

        router.replace({
            path: route.path,
            query
        });
    }

    return {
        project,
        columns,
        loading,
        showIssueForm,
        selectedColumn,
        selectedIssue,
        draggedIssue,
        issueTotal,
        doneTotal,
        issuesByColumn,
        loadBoard,
        openCreateIssue,
        onIssueCreated,
        onIssueChanged,
        onIssueDeleted,
        onDragIssue,
        onDropIssue,
        applyIssueMovedLocal,
        openIssueFromQuery,
        closeIssueModal,
    };
}