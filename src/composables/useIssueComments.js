import { computed, ref } from "vue";

import { commentApi, getErrorMessage } from "../services/api";
import { normalizeMember } from "../utils/memberUtils";
import {
  extractMentionedUserIdsFromText as extractMentionIds,
  highlightMentions,
} from "../utils/mentionUtils";
import { useToast } from "./useToast";

const MENTION_LIMIT = 6;
const MENTION_PATTERN = /(^|\s)@([^\s@]*)$/;

export function useIssueComments({ props, error }) {
  const comments = ref([]);
  const commentText = ref("");
  const commentLoading = ref(false);

  const commentBoxRef = ref(null);

  const mentionedUserIds = ref([]);
  const mentionQuery = ref("");
  const mentionStartIndex = ref(-1);
  const showMentionSuggestions = ref(false);
  const activeMentionIndex = ref(0);

  const toast = useToast();

  const mentionableMembers = computed(() => {
    return props.members.map(normalizeMember).filter(Boolean);
  });

  const mentionSuggestions = computed(() => {
    const query = mentionQuery.value.trim().toLowerCase();

    return mentionableMembers.value
      .filter((member) => isMentionMatch(member, query))
      .slice(0, MENTION_LIMIT);
  });

  async function loadComments() {
    try {
      comments.value = await commentApi.list(props.issue.id);
    } catch (err) {
      const message = getErrorMessage(err);
      error.value = message;
      toast.error(message);
    }
  }

  async function addComment() {
    const body = commentText.value.trim();

    if (!body || commentLoading.value) return;

    commentLoading.value = true;
    error.value = "";

    try {
      await commentApi.create(props.issue.id, {
        body,
        mentioned_user_ids: extractMentionedUserIdsFromText(),
      });

      resetCommentForm();
      await loadComments();
    } catch (err) {
      const message = getErrorMessage(err);
      error.value = message;
      toast.error(message);
    } finally {
      commentLoading.value = false;
    }
  }

  function handleCommentInput(event) {
    const textarea = event.target;
    const cursorPosition = textarea.selectionStart;
    const textBeforeCursor = commentText.value.slice(0, cursorPosition);
    const mentionMatch = textBeforeCursor.match(MENTION_PATTERN);

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

  function handleCommentKeydown(event) {
    if (!showMentionSuggestions.value || mentionSuggestions.value.length === 0) {
      return;
    }

    const handlers = {
      ArrowDown: () => moveActiveMention(1),
      ArrowUp: () => moveActiveMention(-1),
      Enter: () => insertMention(mentionSuggestions.value[activeMentionIndex.value]),
      Escape: closeMentionSuggestions,
    };

    const handler = handlers[event.key];

    if (!handler) return;

    event.preventDefault();
    handler();
  }

  function handleMentionBlur() {
    window.setTimeout(closeMentionSuggestions, 150);
  }

  function insertMention(member) {
    if (!member || mentionStartIndex.value < 0) return;

    const textarea = commentBoxRef.value;
    const cursorPosition = textarea?.selectionStart ?? commentText.value.length;

    const beforeMention = commentText.value.slice(0, mentionStartIndex.value);
    const afterMention = commentText.value.slice(cursorPosition);
    const mentionText = `@${member.full_name} `;

    commentText.value = `${beforeMention}${mentionText}${afterMention}`;
    addMentionedUserId(member.id);
    closeMentionSuggestions();

    focusCommentBox(beforeMention.length + mentionText.length);
  }

  function closeMentionSuggestions() {
    mentionQuery.value = "";
    mentionStartIndex.value = -1;
    showMentionSuggestions.value = false;
    activeMentionIndex.value = 0;
  }

  function extractMentionedUserIdsFromText() {
    return extractMentionIds(
      commentText.value,
      mentionableMembers.value,
      mentionedUserIds.value
    );
  }

  function resetCommentForm() {
    commentText.value = "";
    mentionedUserIds.value = [];
    closeMentionSuggestions();
  }

  function moveActiveMention(direction) {
    const total = mentionSuggestions.value.length;

    if (total === 0) return;

    activeMentionIndex.value = (activeMentionIndex.value + direction + total) % total;
  }

  function addMentionedUserId(userId) {
    const id = Number(userId);

    if (!Number.isFinite(id)) return;

    if (!mentionedUserIds.value.includes(id)) {
      mentionedUserIds.value.push(id);
    }
  }

  function focusCommentBox(cursorPosition) {
    window.setTimeout(() => {
      commentBoxRef.value?.focus();
      commentBoxRef.value?.setSelectionRange(cursorPosition, cursorPosition);
    }, 0);
  }

  return {
    comments,
    commentText,
    commentLoading,

    commentBoxRef,
    mentionedUserIds,
    mentionQuery,
    mentionStartIndex,
    showMentionSuggestions,
    activeMentionIndex,
    mentionableMembers,
    mentionSuggestions,

    loadComments,
    addComment,
    handleCommentInput,
    handleCommentKeydown,
    handleMentionBlur,
    insertMention,
    closeMentionSuggestions,
    extractMentionedUserIdsFromText,
    highlightMentions,
  };
}

function isMentionMatch(member, query) {
  const name = member.full_name?.toLowerCase() || "";
  const email = member.email?.toLowerCase() || "";

  return !query || name.includes(query) || email.includes(query);
}
