<script setup>
import { computed, ref } from "vue";
import { Save, Trash2 } from "lucide-vue-next";

import ModalShell from "./ModalShell.vue";
import IssueActivitySection from "./issue-detail/IssueActivitySection.vue";
import IssueAttachmentsSection from "./issue-detail/IssueAttachmentsSection.vue";
import IssueChecklistSection from "./issue-detail/IssueChecklistSection.vue";
import IssueCommentsSection from "./issue-detail/IssueCommentsSection.vue";
import IssuePropertiesSidebar from "./issue-detail/IssuePropertiesSidebar.vue";

import { useIssueForm } from "../composables/useIssueForm";
import { useIssuePlanning } from "../composables/useIssuePlanning";
import { normalizeMember } from "../utils/memberUtils";

const props = defineProps({
  projectId: { type: [String, Number], required: true },
  issue: { type: Object, required: true },
  members: { type: Array, default: () => [] },
  canEdit: { type: Boolean, default: true },
  projectLabels: { type: Array, default: () => [] },
  epics: { type: Array, default: () => [] },
  sprints: { type: Array, default: () => [] },
});

const emit = defineEmits(["close", "changed", "deleted"]);
const error = ref("");

const { loading, deleting, form, saveIssue, deleteIssue } = useIssueForm({
  props,
  emit,
  error,
});

const assigneeName = computed(() => {
  if (!props.issue.assignee_id) return "Unassigned";

  const member = props.members
    .map(normalizeMember)
    .find((item) => Number(item.id) === Number(props.issue.assignee_id));

  return member?.full_name || "Unassigned";
});

const reporter = computed(() => {
  if (!props.issue.reporter_id) return null;

  return props.members
    .map(normalizeMember)
    .find((member) => Number(member.id) === Number(props.issue.reporter_id));
});

const { updateIssueEpic, updateIssueSprint } = useIssuePlanning({
  props,
  form,
  error,
  loadIssueActivities: () => {},
});
</script>

<template>
  <ModalShell
    :title="issue.code"
    :subtitle="`Assigned to ${assigneeName}`"
    wide
    @close="emit('close')"
  >
    <div class="grid gap-6 lg:grid-cols-[1fr_320px]">
      <div class="space-y-4">
        <div>
          <label class="label">Title</label>
          <input
            v-model="form.title"
            :disabled="!canEdit"
            class="input text-base font-bold"
          />
        </div>

        <div>
          <label class="label">Description</label>
          <textarea
            v-model="form.description"
            :disabled="!canEdit"
            class="input min-h-44 resize-none"
          ></textarea>
        </div>

        <p
          v-if="error"
          class="rounded-xl bg-rose-50 px-4 py-3 text-sm font-medium text-rose-700"
        >
          {{ error }}
        </p>

        <div class="flex flex-wrap gap-3">
          <button
            v-if="canEdit"
            class="btn-primary"
            :disabled="loading"
            @click="saveIssue"
          >
            <Save class="h-4 w-4" />
            {{ loading ? "Saving..." : "Save changes" }}
          </button>

          <button
            v-if="canEdit"
            class="btn-danger"
            :disabled="deleting"
            @click="deleteIssue"
          >
            <Trash2 class="h-4 w-4" />
            {{ deleting ? "Deleting..." : "Delete" }}
          </button>
        </div>

        <IssueChecklistSection :issue="issue" :can-edit="canEdit" />
        <IssueAttachmentsSection :issue="issue" :can-edit="canEdit" />
        <IssueCommentsSection :issue="issue" :members="members" :can-edit="canEdit" />
        <IssueActivitySection :issue="issue" />
      </div>

      <IssuePropertiesSidebar
        :issue="issue"
        :form="form"
        :members="members"
        :project-labels="projectLabels"
        :epics="epics"
        :sprints="sprints"
        :can-edit="canEdit"
        :reporter="reporter"
        @update-epic="updateIssueEpic"
        @update-sprint="updateIssueSprint"
      />
    </div>
  </ModalShell>
</template>
