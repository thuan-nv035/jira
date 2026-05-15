import { computed, ref } from "vue";
import { authApi, getErrorMessage, projectApi } from "../services/api";
import { normalizeMember } from "../utils/memberUtils";
import { useToast } from "./useToast";
export function useProjectMembers({ projectId, project, error }) {
  const currentUser = ref(null);
  const members = ref([]);
  const showAddMember = ref(false);
  const MAX_VISIBLE_AVATARS = 9;
  const toast = useToast();
  const projectMemberAvatars = computed(() => members.value.map(normalizeMember).filter(Boolean));
  const visibleProjectMembers = computed(() => projectMemberAvatars.value.slice(0, MAX_VISIBLE_AVATARS));
  const hiddenProjectMemberCount = computed(() => Math.max(projectMemberAvatars.value.length - MAX_VISIBLE_AVATARS, 0));

  const currentProjectMember = computed(() => {
    if (!currentUser.value) return null;

    return members.value
      .map(normalizeMember)
      .find((member) => Number(member.id) === Number(currentUser.value.id));
  });

  const currentProjectRole = computed(() => {
    if (!currentUser.value || !project.value) return "";

    if (Number(project.value.owner_id) === Number(currentUser.value.id)) return "OWNER";

    return currentProjectMember.value?.role || "";
  });

  const canManageMembers = computed(() => currentProjectRole.value === "OWNER");
  const canManageColumns = computed(() => ["OWNER", "ADMIN"].includes(currentProjectRole.value));
  const canEditIssues = computed(() => ["OWNER", "ADMIN", "MEMBER"].includes(currentProjectRole.value));
  const isViewer = computed(() => currentProjectRole.value === "VIEWER");

  async function loadCurrentUser() {
    try {
      currentUser.value = await authApi.me();
    } catch (err) {
      error.value = getErrorMessage(err);
    }
  }

  async function loadProjectMembers() {
    members.value = await projectApi.members(projectId.value);
  }

  async function updateMemberRole(member, role) {
    if (!canManageMembers.value) return;

    try {
      await projectApi.updateMemberRole(projectId.value, member.id, role);
      await loadProjectMembers();
      window.dispatchEvent(new CustomEvent("jira-dashboard-refresh"));
    } catch (err) {
      error.value = getErrorMessage(err);
      toast.error(error.value);
    }
  }

  async function removeProjectMember(member) {
    if (!canManageMembers.value) return;
    if (!confirm(`Remove ${member.full_name} from this project?`)) return;

    try {
      await projectApi.removeMember(projectId.value, member.id);
      await loadProjectMembers();
      window.dispatchEvent(new CustomEvent("jira-dashboard-refresh"));
    } catch (err) {
      error.value = getErrorMessage(err);
      toast.error(error.value);
    }
  }

  function isProjectOwner(member) {
    return Number(project.value?.owner_id) === Number(member.id);
  }

  function onMemberAdded(member) {
    showAddMember.value = false;
    members.value = [...members.value, member];
  }

  return {
    currentUser,
    members,
    showAddMember,
    projectMemberAvatars,
    visibleProjectMembers,
    hiddenProjectMemberCount,
    currentProjectMember,
    currentProjectRole,
    canManageMembers,
    canManageColumns,
    canEditIssues,
    isViewer,
    loadCurrentUser,
    loadProjectMembers,
    updateMemberRole,
    removeProjectMember,
    isProjectOwner,
    onMemberAdded,
  };
}
