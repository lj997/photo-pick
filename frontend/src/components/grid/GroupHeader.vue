<template>
  <div class="col-span-full flex items-center gap-3 px-4 py-2.5 bg-bg-raised border border-border rounded-xl my-1">
    <div class="w-2 h-2 rounded-full bg-accent"></div>
    <span class="font-medium text-sm text-text-DEFAULT">{{ group.name || '相似组' }}</span>
    <span class="text-xs text-text-muted bg-surface-hover px-2 py-0.5 rounded-full">{{ group.member_count }} 张</span>
    <div class="ml-auto flex items-center gap-2">
      <button
        @click="$emit('enter-pk', group)"
        class="px-3 py-1 rounded-lg text-xs font-medium bg-accent text-white hover:bg-accent-hover transition-colors"
      >PK 对比</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Group } from '../../types/photo'

defineProps<{ group: Group }>()
defineEmits<{ 'enter-pk': [group: Group] }>()
</script>
