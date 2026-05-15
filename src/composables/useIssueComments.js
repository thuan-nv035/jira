import { computed, ref } from "vue";
import { commentApi, getErrorMessage } from "../services/api";
import { normalizeMember } from "../utils/memberUtils";
import { extractMentionedUserIdsFromText as extractIds, highlightMentions } from "../utils/mentionUtils";
import { useToast } from "./useToast";
export function useIssueComments({ props, error }) {
  const comments = ref([]);
  const commentText = ref("");
  const commentLoading = ref(false);
  const mentionedUserIds = ref([]);
  const commentBoxRef = ref(null);
  const mentionQuery = ref("");
  const mentionStartIndex = ref(-1);
  const showMentionSuggestions = ref(false);
  const activeMentionIndex = ref(0);
  const toast = useToast();
  
  const mentionableMembers = computed(() => props.members.map(normalizeMember).filter(Boolean));

  const mentionSuggestions = computed(() => {
    const query = mentionQuery.value.trim().toLowerCase();

    const users = mentionableMembers.value.filter((member) => {
      const name = member.full_name?.toLowerCase() || "";
      const email = member.email?.toLowerCase() || "";
      if (!query) return true;
      return name.includes(query) || email.includes(query);
    });

    return users.slice(0, 6);
  });

  async function loadComments() {
    comments.value = await commentApi.list(props.issue.id);
  }

  function closeMentionSuggestions() {
    mentionQuery.value = "";
    mentionStartIndex.value = -1;
    showMentionSuggestions.value = false;
    activeMentionIndex.value = 0;
  }

  function extractMentionedUserIdsFromText() {
    return extractIds(commentText.value, mentionableMembers.value, mentionedUserIds.value);
  }

  async function addComment() {
    if (!commentText.value.trim()) return;

    commentLoading.value = true;
    error.value = "";

    try {
      await commentApi.create(props.issue.id, {
        body: commentText.value.trim(),
        mentioned_user_ids: extractMentionedUserIdsFromText(),
      });

      commentText.value = "";
      mentionedUserIds.value = [];
      closeMentionSuggestions();
      await loadComments();
    } catch (err) {
      error.value = getErrorMessage(err);
      toast.error(error.value);
    } finally {
      commentLoading.value = false;
    }
  }

  function handleMentionBlur() {
    window.setTimeout(() => closeMentionSuggestions(), 150);
  }

  function handleCommentInput(event) {
    const textarea = event.target;
    const cursorPosition = textarea.selectionStart;
    const textBeforeCursor = commentText.value.slice(0, cursorPosition);
    const mentionMatch = textBeforeCursor.match(/(^|\s)@([^\s@]*)$/);

    if (!mentionMatch) {
      closeMentionSuggestions();
      return;
    }

    const query = mentionMatch[2] || "";
    mentionQuery.value = query;
    mentionStartIndex.value = cursorPosition - query.length - 1;
    showMentionSuggestions.value = true;
    activeMentionIndex.value = 0;
  }

  function insertMention(member) {
    if (!member || mentionStartIndex.value < 0) return;

    const textarea = commentBoxRef.value;
    const cursorPosition = textarea?.selectionStart ?? commentText.value.length;
    const beforeMention = commentText.value.slice(0, mentionStartIndex.value);
    const afterMention = commentText.value.slice(cursorPosition);
    const mentionText = `@${member.full_name} `;

    commentText.value = `${beforeMention}${mentionText}${afterMention}`;

    const id = Number(member.id);
    if (!mentionedUserIds.value.includes(id)) mentionedUserIds.value.push(id);

    closeMentionSuggestions();

    setTimeout(() => {
      const nextCursorPosition = beforeMention.length + mentionText.length;
      commentBoxRef.value?.focus();
      commentBoxRef.value?.setSelectionRange(nextCursorPosition, nextCursorPosition);
    }, 0);
  }

  function handleCommentKeydown(event) {
    if (!showMentionSuggestions.value || mentionSuggestions.value.length === 0) return;

    if (event.key === "ArrowDown") {
      event.preventDefault();
      activeMentionIndex.value = (activeMentionIndex.value + 1) % mentionSuggestions.value.length;
    }

    if (event.key === "ArrowUp") {
      event.preventDefault();
      activeMentionIndex.value = activeMentionIndex.value === 0 ? mentionSuggestions.value.length - 1 : activeMentionIndex.value - 1;
    }

    if (event.key === "Enter") {
      event.preventDefault();
      insertMention(mentionSuggestions.value[activeMentionIndex.value]);
    }

    if (event.key === "Escape") {
      event.preventDefault();
      closeMentionSuggestions();
    }
  }

  return {
    comments,
    commentText,
    commentLoading,
    mentionedUserIds,
    commentBoxRef,
    mentionQuery,
    mentionStartIndex,
    showMentionSuggestions,
    activeMentionIndex,
    mentionableMembers,
    mentionSuggestions,
    loadComments,
    addComment,
    handleMentionBlur,
    handleCommentInput,
    closeMentionSuggestions,
    insertMention,
    handleCommentKeydown,
    extractMentionedUserIdsFromText,
    highlightMentions,
  };
}
