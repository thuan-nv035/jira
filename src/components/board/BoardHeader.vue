<script setup>
import {
  ArrowLeft,
  Activity,
  Plus,
  RefreshCcw,
  UserPlus,
  Wifi,
  WifiOff,
} from "lucide-vue-next";
import { getInitials, getAvatarColorClass } from "../../utils/memberUtils";

const props = defineProps({
  project: { type: Object, default: null },
  socketStatus: { type: String, default: "disconnected" },
  avatars: { type: Array, default: () => [] },
  visibleAvatars: { type: Array, default: () => [] },
  hiddenCount: { type: Number, default: 0 },
  canCreateIssue: { type: Boolean, default: true },
  canAddMember: { type: Boolean, default: false },
  hasColumns: { type: Boolean, default: false },
});

const emit = defineEmits([
  "back",
  "refresh",
  "add-member",
  "dashboard",
  "create-issue",
]);
</script>

<template>
  <div
    class="mb-5 flex flex-col gap-4 xl:flex-row xl:items-end xl:justify-between"
  >
    <div>
      <button
        class="mb-4 inline-flex items-center gap-2 text-sm font-bold text-slate-500 hover:text-slate-950"
        @click="emit('back')"
      >
        <ArrowLeft class="h-4 w-4" />
        Back to projects
      </button>

      <div class="flex flex-wrap items-center gap-3">
        <span
          class="rounded-full bg-blue-50 px-3 py-1 text-xs font-black text-blue-700"
        >
          {{ project?.key || "PROJECT" }}
        </span>

        <span
          :class="[
            'inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-black',
            socketStatus === 'connected'
              ? 'bg-emerald-50 text-emerald-700'
              : 'bg-slate-100 text-slate-500',
          ]"
        >
          <Wifi v-if="socketStatus === 'connected'" class="h-3.5 w-3.5" />
          <WifiOff v-else class="h-3.5 w-3.5" />
          {{ socketStatus }}
        </span>

        <div
          v-if="avatars.length > 0"
          class="flex items-center gap-3 rounded-full bg-white px-3 py-2 shadow-sm ring-1 ring-slate-200"
        >
          <div class="flex -space-x-2">
            <div
              v-for="(member, index) in visibleAvatars"
              :key="member.id || index"
              class="group relative"
            >
              <div
                class="flex h-9 w-9 items-center justify-center overflow-hidden rounded-full border-2 border-white text-xs font-black text-white shadow-sm ring-1 ring-slate-200 transition hover:z-10 hover:scale-110"
                :class="!member.avatar_url ? getAvatarColorClass(index) : ''"
                :title="member.full_name"
              >
                <img
                  v-if="member.avatar_url"
                  :src="member.avatar_url"
                  :alt="member.full_name"
                  class="h-full w-full object-cover"
                />
                <span v-else>{{ getInitials(member.full_name) }}</span>
              </div>

              <div
                class="pointer-events-none absolute left-1/2 top-11 z-50 hidden w-max -translate-x-1/2 rounded-xl bg-slate-950 px-3 py-2 text-xs font-bold text-white shadow-xl group-hover:block"
              >
                {{ member.full_name }}
                <div
                  v-if="member.email"
                  class="mt-0.5 text-[11px] font-medium text-slate-300"
                >
                  {{ member.email }}
                </div>
              </div>
            </div>

            <div
              v-if="hiddenCount > 0"
              class="flex h-9 w-9 items-center justify-center rounded-full border-2 border-white bg-slate-100 text-xs font-black text-slate-600 shadow-sm ring-1 ring-slate-200"
              :title="`${hiddenCount} more member(s)`"
            >
              ...
            </div>
          </div>

          <span class="text-sm font-black text-slate-700">
            {{ avatars.length }}
          </span>
        </div>
      </div>

      <h1 class="mt-3 text-3xl font-black tracking-tight text-slate-950">
        {{ project?.name || "Board" }}
      </h1>

      <p class="mt-2 max-w-2xl text-sm leading-6 text-slate-500">
        {{
          project?.description ||
          "Manage issues by dragging cards between columns."
        }}
      </p>
    </div>

    <div class="flex flex-wrap gap-3">
      <button class="btn-secondary" @click="emit('refresh')">
        <RefreshCcw class="h-4 w-4" />
        Refresh
      </button>

      <button
        v-if="canAddMember"
        class="btn-secondary"
        @click="emit('add-member')"
      >
        <UserPlus class="h-4 w-4" />
        Add member
      </button>

      <button class="btn-secondary" @click="emit('dashboard')">
        <Activity class="h-4 w-4" />
        Dashboard
      </button>

      <button
        v-if="canCreateIssue"
        class="btn-primary"
        :disabled="!hasColumns"
        @click="emit('create-issue')"
      >
        <Plus class="h-4 w-4" />
        Create issue
      </button>
    </div>
  </div>
</template>
