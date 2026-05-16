<script setup>
import { onMounted, ref } from "vue";
import { MessageCircle } from "lucide-vue-next";

import { useIssueComments } from "../../composables/useIssueComments";
import { formatDateTime } from "../../utils/dateUtils";
import { getInitials } from "../../utils/memberUtils";

const props = defineProps({
  issue: {
    type: Object,
    required: true,
  },
  members: {
    type: Array,
    default: () => [],
  },
  canEdit: {
    type: Boolean,
    default: true,
  },
});

const error = ref("");

const {
  comments,
  commentText,
  commentLoading,
  commentBoxRef,
  showMentionSuggestions,
  activeMentionIndex,
  mentionSuggestions,
  loadComments,
  addComment,
  handleCommentBlur,
  handleCommentInput,
  insertMention,
  handleCommentKeydown,
  highlightMentions,
} = useIssueComments({
  props,
  error,
});

onMounted(loadComments);
</script>

<template>
  <section class="rounded-2xl border border-slate-200 bg-slate-50 p-4">
    <div class="mb-4 flex items-center gap-2">
      <MessageCircle class="h-5 w-5 text-slate-500" />
      <h3 class="font-black text-slate-950">Comments</h3>
    </div>

    <p
      v-if="error"
      class="mb-3 rounded-xl bg-rose-50 px-4 py-3 text-sm font-medium text-rose-700"
    >
      {{ error }}
    </p>

    <form
      v-if="canEdit"
      class="mb-4 flex w-full gap-2"
      @submit.prevent="addComment"
    >
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
              <p class="truncate text-sm font-black text-slate-900">
                {{ member.full_name }}
              </p>
              <p class="truncate text-xs text-slate-400">
                {{ member.email }}
              </p>
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

      <button
        type="submit"
        class="btn-primary whitespace-nowrap"
        :disabled="commentLoading || !commentText.trim()"
      >
        {{ commentLoading ? "Sending..." : "Send" }}
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
            {{ formatDateTime(comment.created_at) }}
          </p>
        </div>

        <p
          class="text-sm text-slate-700"
          v-html="highlightMentions(comment.body)"
        ></p>
      </div>

      <p
        v-if="comments.length === 0"
        class="rounded-2xl bg-white p-4 text-sm text-slate-500"
      >
        No comments yet.
      </p>
    </div>
  </section>
</template>
