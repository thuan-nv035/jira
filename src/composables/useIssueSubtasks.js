import {
    computed,
    ref
} from "vue";
import {
    getErrorMessage,
    subtaskApi
} from "../services/api";
import {
    normalizeMember
} from "../utils/memberUtils";
import {
    useToast
} from "./useToast";

export function useIssueSubtasks({
    props,
    error,
    loadIssueActivities
}) {
    const toast = useToast();

    const subtasks = ref([]);
    const subtaskLoading = ref(false);
    const subtaskSaving = ref(false);

    const newSubtaskTitle = ref("");
    const newSubtaskAssigneeId = ref("");

    const editingSubtaskId = ref(null);
    const editingSubtaskTitle = ref("");
    const editingSubtaskAssigneeId = ref("");

    const subtaskTotal = computed(() => subtasks.value.length);

    const subtaskDone = computed(() => {
        return subtasks.value.filter((item) => item.is_done).length;
    });

    const subtaskPercent = computed(() => {
        if (subtaskTotal.value === 0) return 0;

        return Math.round((subtaskDone.value * 100) / subtaskTotal.value);
    });

    const assigneeOptions = computed(() => {
        return props.members.map(normalizeMember).filter(Boolean);
    });

    async function loadSubtasks() {
        if (!props.issue ?.id) return;

        subtaskLoading.value = true;

        try {
            subtasks.value = await subtaskApi.list(props.issue.id);
        } catch (err) {
            setError(err);
        } finally {
            subtaskLoading.value = false;
        }
    }

    async function createSubtask() {
        if (!props.canEdit) return;

        const title = newSubtaskTitle.value.trim();

        if (!title) return;

        subtaskSaving.value = true;
        error.value = "";

        try {
            await subtaskApi.create(props.issue.id, {
                title,
                assignee_id: newSubtaskAssigneeId.value ?
                    Number(newSubtaskAssigneeId.value) :
                    null
            });

            newSubtaskTitle.value = "";
            newSubtaskAssigneeId.value = "";

            await loadSubtasks();
            await refreshActivity();

            toast.success("Subtask created");
        } catch (err) {
            setError(err);
        } finally {
            subtaskSaving.value = false;
        }
    }

    async function toggleSubtask(subtask) {
        if (!props.canEdit) return;

        const oldValue = subtask.is_done;
        const nextValue = !oldValue;

        subtask.is_done = nextValue;

        try {
            await subtaskApi.update(subtask.id, {
                is_done: nextValue
            });

            await refreshActivity();
        } catch (err) {
            subtask.is_done = oldValue;
            setError(err);
        }
    }

    function startEditSubtask(subtask) {
        if (!props.canEdit) return;

        editingSubtaskId.value = subtask.id;
        editingSubtaskTitle.value = subtask.title;
        editingSubtaskAssigneeId.value = subtask.assignee_id || "";
    }

    function cancelEditSubtask() {
        editingSubtaskId.value = null;
        editingSubtaskTitle.value = "";
        editingSubtaskAssigneeId.value = "";
    }

    async function saveEditSubtask(subtask) {
        if (!props.canEdit) return;

        const title = editingSubtaskTitle.value.trim();

        if (!title) {
            error.value = "Subtask title is required";
            toast.error(error.value);
            return;
        }

        try {
            await subtaskApi.update(subtask.id, {
                title,
                assignee_id: editingSubtaskAssigneeId.value ?
                    Number(editingSubtaskAssigneeId.value) :
                    null
            });

            cancelEditSubtask();

            await loadSubtasks();
            await refreshActivity();

            toast.success("Subtask updated");
        } catch (err) {
            setError(err);
        }
    }

    async function deleteSubtask(subtask) {
        if (!props.canEdit) return;

        if (!window.confirm(`Delete subtask "${subtask.title}"?`)) return;

        try {
            await subtaskApi.remove(subtask.id);

            subtasks.value = subtasks.value.filter((item) => item.id !== subtask.id);

            await refreshActivity();

            toast.success("Subtask deleted");
        } catch (err) {
            setError(err);
        }
    }

    function getSubtaskAssigneeName(subtask) {
        if (subtask.assignee ?.full_name) return subtask.assignee.full_name;

        const assignee = assigneeOptions.value.find((member) => {
            return Number(member.id) === Number(subtask.assignee_id);
        });

        return assignee ?.full_name || "Unassigned";
    }

    function onSubtaskRealtime(event) {
        const issueId = Number(event.detail ?.issue_id);

        if (!issueId || issueId === Number(props.issue.id)) {
            loadSubtasks();
        }
    }

    async function refreshActivity() {
        if (!loadIssueActivities) return;

        await loadIssueActivities({
            reset: true,
            silent: true
        });
    }

    function setError(err) {
        const message = getErrorMessage(err);
        error.value = message;
        toast.error(message);
    }

    return {
        subtasks,
        subtaskLoading,
        subtaskSaving,
        newSubtaskTitle,
        newSubtaskAssigneeId,
        editingSubtaskId,
        editingSubtaskTitle,
        editingSubtaskAssigneeId,
        subtaskTotal,
        subtaskDone,
        subtaskPercent,
        assigneeOptions,
        loadSubtasks,
        createSubtask,
        toggleSubtask,
        startEditSubtask,
        cancelEditSubtask,
        saveEditSubtask,
        deleteSubtask,
        getSubtaskAssigneeName,
        onSubtaskRealtime
    };
}