<template>
  <div class="h-full flex flex-col">
    <!-- Grid area -->
    <div class="flex-1 overflow-y-auto p-3">
      <div
        v-if="loading"
        class="h-full flex flex-col items-center justify-center gap-3"
      >
        <div class="w-8 h-8 border-[3px] border-border border-t-accent rounded-full animate-spin"></div>
        <span class="text-text-muted text-sm">正在加载照片...</span>
      </div>
      <div
        v-else-if="photos.photos.length === 0 && groupsStore.groups.length === 0"
        class="h-full flex flex-col items-center justify-center gap-2"
      >
        <span class="text-3xl">&#128247;</span>
        <span class="text-text-muted text-sm">暂无照片</span>
      </div>

      <!-- 分组模式 -->
      <div
        v-else-if="ui.gridMode === 'grouped' && groupsStore.groups.length > 0"
        class="grid gap-3"
        :style="{ gridTemplateColumns: 'repeat(' + columns + ', 1fr)' }"
      >
        <template v-for="(group, gIdx) in groupsStore.groups" :key="group.id">
          <GroupHeader :group="group" @enter-pk="onEnterPK(gIdx)" />
          <PhotoTile
            v-for="photo in (group.members || [])"
            :key="photo.id"
            :photo="photo"
            :selected="false"
            @click="selectGroupPhoto(photo.id)"
            @dblclick="openGroupViewer(photo.id)"
            @mark="(marks) => onMark(photo.id, marks)"
          />
        </template>
      </div>

      <!-- 平铺模式 -->
      <div
        v-else
        class="grid gap-3"
        :style="{ gridTemplateColumns: 'repeat(' + columns + ', 1fr)' }"
      >
        <PhotoTile
          v-for="(photo, idx) in photos.photos"
          :key="photo.id"
          :photo="photo"
          :selected="photos.currentIndex === idx"
          @click="selectPhoto(idx)"
          @dblclick="openViewer(idx)"
          @mark="(marks) => onMark(photo.id, marks)"
        />
      </div>
    </div>

    <!-- Pagination bar (仅平铺模式) -->
    <div v-if="ui.gridMode === 'flat'" class="h-11 flex items-center justify-between px-4 bg-bg-raised border-t border-border shrink-0">
      <div class="flex items-center gap-2 text-sm text-text-secondary">
        <span>每页</span>
        <select
          :value="photos.pageSize"
          @change="onPageSizeChange"
          class="bg-bg-raised border border-border rounded-lg px-2 py-0.5 text-text-DEFAULT text-sm"
        >
          <option :value="20">20</option>
          <option :value="50">50</option>
          <option :value="100">100</option>
          <option :value="200">200</option>
        </select>
        <span>张</span>
        <span class="ml-2 text-text-muted">共 {{ photos.total }} 张</span>
      </div>

      <div class="flex items-center gap-1">
        <button
          @click="photos.goToPage(1)"
          :disabled="photos.page <= 1"
          class="px-2 py-1 rounded-lg text-sm disabled:opacity-30 text-text-secondary hover:text-text-DEFAULT hover:bg-surface-hover transition-all"
        >
          &laquo;
        </button>
        <button
          @click="photos.prevPage()"
          :disabled="photos.page <= 1"
          class="px-2 py-1 rounded-lg text-sm disabled:opacity-30 text-text-secondary hover:text-text-DEFAULT hover:bg-surface-hover transition-all"
        >
          &lsaquo;
        </button>

        <template v-for="p in visiblePages" :key="p">
          <button
            v-if="p === '...'"
            disabled
            class="px-2 py-1 text-sm text-text-muted"
          >
            ...
          </button>
          <button
            v-else
            @click="photos.goToPage(p as number)"
            :class="[
              'px-2.5 py-1 rounded-lg text-sm font-medium transition-all',
              photos.page === p ? 'bg-accent text-white shadow-sm' : 'text-text-DEFAULT hover:bg-surface-hover'
            ]"
          >
            {{ p }}
          </button>
        </template>

        <button
          @click="photos.nextPage()"
          :disabled="photos.page >= photos.totalPages"
          class="px-2 py-1 rounded-lg text-sm disabled:opacity-30 text-text-secondary hover:text-text-DEFAULT hover:bg-surface-hover transition-all"
        >
          &rsaquo;
        </button>
        <button
          @click="photos.goToPage(photos.totalPages)"
          :disabled="photos.page >= photos.totalPages"
          class="px-2 py-1 rounded-lg text-sm disabled:opacity-30 text-text-secondary hover:text-text-DEFAULT hover:bg-surface-hover transition-all"
        >
          &raquo;
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { usePhotosStore } from '../../stores/photos'
import { useUIStore } from '../../stores/ui'
import { useGroupsStore } from '../../stores/groups'
import PhotoTile from './PhotoTile.vue'
import GroupHeader from './GroupHeader.vue'

const photos = usePhotosStore()
const ui = useUIStore()
const groupsStore = useGroupsStore()

const columns = computed(() => ui.gridColumns)
const loading = computed(() => photos.loading)

const visiblePages = computed(() => {
  const total = photos.totalPages
  const current = photos.page
  const pages: (number | string)[] = []

  if (total <= 7) {
    for (let i = 1; i <= total; i++) pages.push(i)
    return pages
  }

  pages.push(1)
  if (current > 3) pages.push('...')

  const start = Math.max(2, current - 1)
  const end = Math.min(total - 1, current + 1)
  for (let i = start; i <= end; i++) pages.push(i)

  if (current < total - 2) pages.push('...')
  pages.push(total)

  return pages
})

function selectPhoto(idx: number) {
  photos.setCurrentIndex(idx)
}

function openViewer(idx: number) {
  photos.setCurrentIndex(idx)
  ui.setViewMode('viewer')
}

function selectGroupPhoto(_photoId: string) {
  // 分组模式下单击暂无特殊行为
}

function openGroupViewer(_photoId: string) {
  // 分组模式下双击暂无特殊行为
}

function onEnterPK(groupIndex: number) {
  groupsStore.enterGroup(groupIndex)
  ui.setViewMode('pk')
}

async function onMark(photoId: string, marks: { stars?: number; color_label?: string; status?: string }) {
  await photos.setMark(photoId, marks)
  groupsStore.updateMemberPhoto(photoId, marks as any)
}

function onPageSizeChange(e: Event) {
  const val = parseInt((e.target as HTMLSelectElement).value)
  photos.setPageSize(val)
}
</script>
