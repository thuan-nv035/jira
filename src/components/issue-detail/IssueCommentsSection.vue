<script setup>
import { computed, onMounted, ref } from "vue";
import { MessageCircle } from "lucide-vue-next";
import { commentApi, getErrorMessage } from "../../services/api";
import { getInitials, normalizeMember } from "../../utils/memberUtils";
import { highlightMentions, extractMentionedUserIdsFromText as buildMentionedUserIds } from "../../utils/mentionUtils";

const props = defineProps({
  issue: { type: Object, required: true },
  members: { type: Array, default: () => [] },
  canEdit: { type: Boolean, default: true },
});

const comments = ref([]);
const commentText = ref("");
const loading = ref(false);
const error = ref("");
const mentionedUserIds = ref([]);
const commentBoxRef = ref(null);
const mentionQuery = ref("");
const mentionStartIndex = ref(-1);
const showMentionSuggestions = ref(false);
const activeMentionIndex = ref(0);

const mentionableMembers = computed(() => props.members.map(normalizeMember).filter(Boolean));

const mentionSuggestions = computed(() => {
  const query = mentionQuery.value.trim().toLowerCase();

  return mentionableMembers.value
    .filter((member) => {
      const name = member.full_name?.toLowerCase() || "";
      const email = member.email?.toLowerCase() || "";
      return !query || name.includes(query) || email.includes(query);
    })
    .slice(0, 6);
});

async function loadComments() {
  try {
    comments.value = await commentApi.list(props.issue.id);
  } catch (err) {
    error.value = getErrorMessage(err);
  }
}

function handleMentionBlur() {
  window.setTimeout(() => {
    closeMentionSuggestions();
  }, 150);
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

function closeMentionSuggestions() {
  mentionQuery.value = "";
  mentionStartIndex.value = -1;
  showMentionSuggestions.value = false;
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

  window.setTimeout(() => {
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
    activeMentionIndex.value =
      activeMentionIndex.value === 0 ? mentionSuggestions.value.length - 1 : activeMentionIndex.value - 1;
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

async function addComment() {
  const body = commentText.value.trim();
  if (!body) return;

  loading.value = true;
  error.value = "";

  try {
    await commentApi.create(props.issue.id, {
      body,
      mentioned_user_ids: extractMentionedUserIdsFromText(),
    });

    commentText.value = "";
    mentionedUserIds.value = [];
    closeMentionSuggestions();
    await loadComments();
  } catch (err) {
    error.value = getErrorMessage(err);
  } finally {
    loading.value = false;
  }
}

onMounted(loadComments);
</script>

<template>
  <section class="rounded-2xl border border-slate-200 bg-slate-50 p-4">
    <div class="mb-4 flex items-center gap-2">
      <MessageCircle class="h-5 w-5 text-slate-500" />
      <h3 class="font-black text-slate-950">Comments</h3>
    </div>

    <p v-if="error" class="mb-3 rounded-xl bg-rose-50 px-4 py-3 text-sm font-medium text-rose-700">
      {{ error }}
    </p>

    <form v-if="canEdit" class="mb-4 flex w-full gap-2" @submit.prevent="addComment">
      <div class="relative w-full">
        <textarea
          ref="commentBoxRef"
          v-model="commentText"
          rows="2"
          placeholder="Write a comment... Type @ to mention someone"
          class="w-full resize-none rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm font-semibold text-slate-700 outline-none transition focus:border-blue-400"
          @input="handleCommentInput"
          @keydown="handleCommentKeydown"
          @blur="handleMentionBlur"
        ></textarea>

        <div
          v-if="showMentionSuggestions && mentionSuggestions.length > 0"
          class="absolute left-3 right-3 top-full z-50 mt-2 overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-xl"
        >
          <button
            v-for="(member, index) in mentionSuggestions"
            :key="member.id"
            type="button"
            class="flex w-full items-center gap-3 px-4 py-3 text-left transition"
            :class="index === activeMentionIndex ? 'bg-blue-50' : 'hover:bg-slate-50'"
            @mousedown.prevent="insertMention(member)"
          >
            <div class="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-slate-900 text-xs font-black text-white">
              {{ getInitials(member.full_name) }}
            </div>

            <div class="min-w-0">
              <p class="truncate text-sm font-black text-slate-900">{{ member.full_name }}</p>
              <p class="truncate text-xs text-slate-400">{{ member.email }}</p>
            </div>
          </button>
        </div>

        <div
          v-if="showMentionSuggestions && mentionSuggestions.length === 0"
          class="absolute left-3 right-3 top-full z-50 mt-2 rounded-2xl border border-slate-200 bg-white p-4 text-sm font-semibold text-slate-400 shadow-xl"
        >
          No matching users
        </div>
      </div>

      <button class="btn-primary whitespace-nowrap" :disabled="loading">
        Send
      </button>
    </form>

    <div class="space-y-3">
      <div
        v-for="comment in comments"
        :key="comment.id"
        class="rounded-2xl bg-white p-4 shadow-sm"
      >
        <div class="mb-1 flex items-center justify-between gap-2">
          <p class="text-sm font-black text-slate-900">
            {{ comment.author?.full_name || "Unknown" }}
          </p>
          <p class="text-xs text-slate-400">
            {{ new Date(comment.created_at).toLocaleString() }}
          </p>
        </div>

        <p class="text-sm text-slate-700" v-html="highlightMentions(comment.body)"></p>
      </div>

      <p v-if="comments.length === 0" class="rounded-2xl bg-white p-4 text-sm text-slate-500">
        No comments yet.
      </p>
    </div>
  </section>
</template>
