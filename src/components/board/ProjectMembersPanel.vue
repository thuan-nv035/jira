<script setup>
import { getInitials, getAvatarColorClass } from "../../utils/memberUtils";

const props = defineProps({
  members: { type: Array, default: () => [] },
  project: { type: Object, default: null },
  currentRole: { type: String, default: "" },
  canManage: { type: Boolean, default: false },
});

const emit = defineEmits(["update-role", "remove-member"]);

function isOwner(member) {
  return Number(props.project?.owner_id) === Number(member.id);
}
</script>

<template>
  <section class="mb-6 rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
    <div class="mb-4 flex flex-wrap items-center justify-between gap-3">
      <div>
        <h2 class="text-base font-black text-slate-950">Project Members</h2>
        <p class="text-sm text-slate-500">Manage member roles and permissions</p>
      </div>

      <span
        class="rounded-full px-3 py-1 text-xs font-black"
        :class="canManage ? 'bg-slate-900 text-white' : 'bg-slate-100 text-slate-500'"
      >
        Your role: {{ currentRole || "UNKNOWN" }}
      </span>
    </div>

    <div class="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
      <div
        v-for="(member, index) in members"
        :key="member.id"
        class="flex items-center justify-between gap-3 rounded-2xl border border-slate-100 bg-slate-50 p-4"
      >
        <div class="flex min-w-0 items-center gap-3">
          <div
            class="flex h-10 w-10 shrink-0 items-center justify-center overflow-hidden rounded-full text-xs font-black text-white"
            :class="!member.avatar_url ? getAvatarColorClass(index) : ''"
          >
            <img
              v-if="member.avatar_url"
              :src="member.avatar_url"
              :alt="member.full_name"
              class="h-full w-full object-cover"
            />
            <span v-else>{{ getInitials(member.full_name) }}</span>
          </div>

          <div class="min-w-0">
            <p class="truncate text-sm font-black text-slate-900">{{ member.full_name }}</p>
            <p class="truncate text-xs text-slate-400">{{ member.email }}</p>
          </div>
        </div>

        <div class="flex shrink-0 items-center gap-2">
          <span
            v-if="isOwner(member)"
            class="rounded-full bg-slate-900 px-3 py-1 text-xs font-black text-white"
          >
            OWNER
          </span>

          <select
            v-else
            :value="member.role"
            class="rounded-xl border border-slate-200 bg-white px-3 py-2 text-xs font-black text-slate-700 outline-none disabled:cursor-not-allowed disabled:bg-slate-100 disabled:text-slate-400"
            :disabled="!canManage"
            @change="emit('update-role', member, $event.target.value)"
          >
            <option value="ADMIN">ADMIN</option>
            <option value="MEMBER">MEMBER</option>
            <option value="VIEWER">VIEWER</option>
          </select>

          <button
            v-if="canManage && !isOwner(member)"
            type="button"
            class="rounded-xl border border-rose-200 px-3 py-2 text-xs font-black text-rose-500 transition hover:bg-rose-50"
            @click="emit('remove-member', member)"
          >
            Remove
          </button>
        </div>
      </div>
    </div>
  </section>
</template>
