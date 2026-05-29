<template>
  <div class="h-full flex flex-col bg-neutral-950 text-white">
    <!-- Toolbar -->
    <div class="h-16 flex items-center justify-between gap-4 px-4 bg-neutral-950/95 border-b border-white/10 shrink-0">
      <div class="flex min-w-0 items-center gap-3">
        <div class="flex h-9 w-9 items-center justify-center rounded-lg bg-amber-500/15 text-amber-300">
          <Trophy class="h-5 w-5" />
        </div>
        <div class="min-w-0">
          <div class="flex items-center gap-2">
            <span class="truncate text-sm font-semibold">{{ currentGroup?.name || 'PK 对比' }}</span>
            <span class="rounded-full bg-white/10 px-2 py-0.5 text-xs text-white/60">组 {{ groupsStore.currentGroupIndex + 1 }}/{{ groupsStore.groups.length }}</span>
          </div>
          <div class="mt-0.5 flex items-center gap-2 text-xs text-white/45">
            <span>{{ totalMembers }} 张</span>
            <span>{{ champions.length }} 张保留</span>
            <span v-if="rejectedCount">{{ rejectedCount }} 张淘汰</span>
            <span>{{ currentRangeLabel }}</span>
          </div>
        </div>
      </div>

      <div class="flex items-center gap-2 overflow-x-auto">
        <div class="flex shrink-0 items-center rounded-lg border border-white/10 bg-white/5 p-0.5">
          <button
            v-for="n in [2, 3, 4]"
            :key="n"
            @click="groupsStore.pkCompareCount = n"
            :class="['px-2.5 py-1 rounded-md text-xs font-medium transition-colors',
              groupsStore.pkCompareCount === n ? 'bg-accent text-white' : 'text-white/60 hover:bg-white/10 hover:text-white']"
          >{{ n }} 张</button>
        </div>
        <button
          @click="handleReset"
          class="inline-flex shrink-0 items-center gap-1.5 rounded-lg border border-orange-400/20 bg-orange-400/10 px-3 py-1.5 text-xs font-medium text-orange-200 hover:bg-orange-400/20"
          title="清空本组保留/淘汰结果"
        >
          <RotateCcw class="h-3.5 w-3.5" />
          重置本组
        </button>
        <button
          @click="groupsStore.prevGroup()"
          :disabled="groupsStore.currentGroupIndex <= 0"
          class="btn-dark"
          title="上一组 (Shift+←)"
        >
          <ChevronLeft class="h-3.5 w-3.5" />
          上一组
        </button>
        <button
          @click="goNextGroupFriendly"
          :disabled="groupsStore.currentGroupIndex >= groupsStore.groups.length - 1"
          class="btn-dark"
          title="下一组 (Shift+→)"
        >
          下一组
          <ChevronRight class="h-3.5 w-3.5" />
        </button>
        <button
          @click="exitPK"
          class="inline-flex shrink-0 items-center gap-1.5 rounded-lg bg-white/10 px-3 py-1.5 text-xs font-medium text-white/80 hover:bg-white/15 hover:text-white"
        >
          <X class="h-3.5 w-3.5" />
          退出
        </button>
      </div>
    </div>

    <!-- Main compare area -->
    <div class="flex-1 min-h-0 grid gap-px bg-white/10 p-px" :class="photoGridClass">
      <div
        v-for="(photo, idx) in displayPhotos"
        :key="photo.id"
        class="relative flex min-w-0 min-h-0 flex-col bg-neutral-950"
        :class="idx === 0 && hasChampion ? 'ring-1 ring-inset ring-amber-400/40' : ''"
      >
        <div class="absolute left-3 top-3 z-10 flex items-center gap-2">
          <span :class="['flex h-7 min-w-7 items-center justify-center rounded-full px-2 text-xs font-semibold shadow-lg',
            idx === 0 && hasChampion ? 'bg-amber-400 text-neutral-950' : 'bg-black/65 text-white']">
            {{ idx + 1 }}
          </span>
          <span
            v-if="idx === 0 && hasChampion"
            class="inline-flex items-center gap-1 rounded-lg bg-amber-400/95 px-2 py-1 text-xs font-semibold text-neutral-950 shadow-lg"
          >
            <Trophy class="h-3.5 w-3.5" />
            当前保留
          </span>
        </div>

        <div
          v-if="photo.status === 'rejected'"
          class="absolute inset-0 z-10 flex items-center justify-center bg-neutral-950/20 pointer-events-none"
        >
          <div class="-rotate-12 rounded-xl border border-rose-400/35 bg-rose-500/15 px-5 py-2 text-3xl font-bold text-rose-300/70">已淘汰</div>
        </div>

        <div class="flex-1 min-h-0 flex items-center justify-center p-3">
          <img
            :src="getFullPhotoUrl(photo.id)"
            :alt="photo.filename"
            :class="['max-w-full max-h-full object-contain transition-all', photo.status === 'rejected' ? 'opacity-35 grayscale' : '']"
          />
        </div>

        <div class="shrink-0 border-t border-white/10 bg-neutral-900/95 px-3 py-3">
          <div class="mb-3 flex items-start justify-between gap-3">
            <div class="min-w-0">
              <div class="truncate text-xs font-medium text-white">{{ photo.filename }}</div>
              <div class="mt-0.5 text-xs text-white/45">
                <span v-if="photo.aperture">f/{{ photo.aperture }}</span>
                <span v-if="photo.shutter_speed" class="ml-1.5">{{ photo.shutter_speed }}s</span>
                <span v-if="photo.iso" class="ml-1.5">ISO {{ photo.iso }}</span>
                <span v-if="photo.focal_length" class="ml-1.5">{{ photo.focal_length }}mm</span>
              </div>
            </div>
            <div class="flex shrink-0 items-center gap-1 text-[11px] text-white/35">
              <Keyboard class="h-3.5 w-3.5" />
              {{ idx + 1 }} 保留 · Shift+{{ idx + 1 }} 淘汰
            </div>
          </div>

          <div class="flex items-center gap-2">
            <template v-if="photo.status === 'rejected'">
              <button
                @click="handleRejectAction(photo)"
                class="action-btn bg-blue-500/15 text-blue-200 hover:bg-blue-500 hover:text-white"
              >
                <Undo2 class="h-3.5 w-3.5" />
                恢复
              </button>
            </template>
            <template v-else>
              <button
                @click="handleChampionAction(photo)"
                :class="['action-btn',
                  photo.status === 'accepted'
                    ? 'bg-amber-400 text-neutral-950 hover:bg-amber-300'
                    : 'bg-emerald-500/15 text-emerald-200 hover:bg-emerald-500 hover:text-white']"
              >
                <Star class="h-3.5 w-3.5" />
                {{ photo.status === 'accepted' ? '取消保留' : '保留' }}
              </button>
              <button
                v-if="photo.status !== 'accepted'"
                @click="handleRejectAction(photo)"
                class="action-btn bg-rose-500/15 text-rose-200 hover:bg-rose-500 hover:text-white"
              >
                <X class="h-3.5 w-3.5" />
                淘汰
              </button>
            </template>
          </div>
        </div>
      </div>

      <div v-if="displayPhotos.length === 0" class="flex items-center justify-center bg-neutral-950">
        <div class="text-center">
          <ImageOff class="mx-auto mb-2 h-8 w-8 text-white/30" />
          <p class="text-sm text-white/45">本组暂无可对比照片</p>
        </div>
      </div>
    </div>

    <!-- Keepers strip -->
    <div v-if="champions.length > 1" class="shrink-0 border-t border-amber-400/20 bg-neutral-950 px-4 py-3">
      <div class="mb-2 flex items-center justify-between">
        <button class="inline-flex items-center gap-2 text-xs font-semibold text-amber-300" @click="champBarExpanded = !champBarExpanded">
          <Star class="h-3.5 w-3.5" />
          已保留 {{ champions.length }} 张
          <ChevronDown :class="['h-3.5 w-3.5 transition-transform', champBarExpanded ? 'rotate-180' : '']" />
        </button>
        <span class="text-xs text-white/35">点击缩略图查看大图</span>
      </div>
      <div v-show="champBarExpanded" class="flex items-center gap-2 overflow-x-auto">
        <button
          v-for="champ in champions"
          :key="champ.id"
          class="relative h-20 shrink-0 overflow-hidden rounded-lg border-2 border-amber-400/40 transition-colors hover:border-amber-300"
          @click="openChampionLightbox(champ)"
        >
          <img :src="getThumbnailUrl(champ.id, 'lg')" class="h-full w-auto object-cover" />
        </button>
      </div>
    </div>

    <!-- Bottom navigation -->
    <div class="h-11 flex items-center justify-between gap-4 border-t border-white/10 bg-neutral-950 px-4 text-xs text-white/45 shrink-0">
      <div class="flex items-center gap-2">
        <button
          @click="goToPrevBatch"
          :disabled="currentOffset <= 0"
          class="btn-dark"
        >
          <ChevronLeft class="h-3.5 w-3.5" />
          上一批
        </button>
        <button
          @click="goToNextBatch"
          :disabled="!hasNextBatch"
          class="btn-dark"
        >
          下一批
          <ChevronRight class="h-3.5 w-3.5" />
        </button>
      </div>
      <div class="flex items-center gap-3">
        <span>1-4 保留</span>
        <span>Shift+1-4 淘汰/恢复</span>
        <span>←/→ 批次</span>
        <span>Shift+←/→ 组</span>
        <span>Esc 返回网格</span>
      </div>
    </div>

    <!-- Keeper lightbox -->
    <Teleport to="body">
      <div
        v-if="lightboxPhoto"
        class="fixed inset-0 z-[9999] flex items-center justify-center bg-black/90"
        @click.self="lightboxPhoto = null"
      >
        <button
          v-if="champions.length > 1"
          @click="lightboxPrev"
          class="absolute left-4 top-1/2 flex h-11 w-11 -translate-y-1/2 items-center justify-center rounded-full bg-white/10 text-white/80 hover:bg-white/20 hover:text-white"
        >
          <ChevronLeft class="h-5 w-5" />
        </button>

        <div class="relative flex max-h-[90vh] max-w-[92vw] flex-col items-center">
          <img
            :src="getFullPhotoUrl(lightboxPhoto.id)"
            :alt="lightboxPhoto.filename"
            class="max-h-[80vh] max-w-full rounded-lg object-contain"
          />
          <div class="mt-4 flex items-center gap-3 rounded-lg bg-white/10 px-3 py-2">
            <span class="text-xs text-white/45">{{ lightboxIndex + 1 }} / {{ champions.length }}</span>
            <span class="max-w-[50vw] truncate text-sm text-white/85">{{ lightboxPhoto.filename }}</span>
            <button
              @click="removeLightboxChampion"
              class="inline-flex items-center gap-1.5 rounded-lg bg-rose-500/90 px-3 py-1.5 text-sm font-medium text-white hover:bg-rose-500"
            >
              <X class="h-4 w-4" />
              取消保留
            </button>
          </div>
          <button
            @click="lightboxPhoto = null"
            class="absolute right-2 top-2 flex h-8 w-8 items-center justify-center rounded-full bg-black/60 text-white/80 hover:bg-black/80 hover:text-white"
          >
            <X class="h-4 w-4" />
          </button>
        </div>

        <button
          v-if="champions.length > 1"
          @click="lightboxNext"
          class="absolute right-4 top-1/2 flex h-11 w-11 -translate-y-1/2 items-center justify-center rounded-full bg-white/10 text-white/80 hover:bg-white/20 hover:text-white"
        >
          <ChevronRight class="h-5 w-5" />
        </button>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch, onMounted, onUnmounted } from 'vue'
import {
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  ImageOff,
  Keyboard,
  RotateCcw,
  Star,
  Trophy,
  Undo2,
  X,
} from 'lucide-vue-next'
import { useGroupsStore } from '../../stores/groups'
import { useUIStore } from '../../stores/ui'
import { getFullPhotoUrl, getThumbnailUrl } from '../../api/photos'
import type { Photo } from '../../types/photo'

const groupsStore = useGroupsStore()
const ui = useUIStore()

const currentGroup = computed(() => groupsStore.currentGroup)
const champions = computed(() => groupsStore.champions)
const primaryChampion = computed(() => groupsStore.primaryChampion)

const browseOffset = ref(0)
const champBarExpanded = ref(true)
const lightboxPhoto = ref<Photo | null>(null)

const allMembers = computed<Photo[]>(() => currentGroup.value?.members || [])
const totalMembers = computed(() => allMembers.value.length)
const hasChampion = computed(() => champions.value.length > 0)

const challengerPool = computed<Photo[]>(() => {
  return allMembers.value.filter(p => !groupsStore.championIds.includes(p.id))
})

const totalPool = computed(() => hasChampion.value ? challengerPool.value.length : allMembers.value.length)
const challengerSlotCount = computed(() => Math.max(1, groupsStore.pkCompareCount - 1))
const currentOffset = computed(() => browseOffset.value)
const rejectedCount = computed(() => allMembers.value.filter(m => m.status === 'rejected').length)

const displayPhotos = computed<Photo[]>(() => {
  if (hasChampion.value && primaryChampion.value) {
    const challengers = challengerPool.value.slice(browseOffset.value, browseOffset.value + challengerSlotCount.value)
    return [primaryChampion.value, ...challengers]
  }
  return allMembers.value.slice(browseOffset.value, browseOffset.value + groupsStore.pkCompareCount)
})

const photoGridClass = computed(() => {
  const count = Math.max(1, displayPhotos.value.length)
  if (count <= 2) return 'grid-cols-2'
  if (count === 3) return 'grid-cols-3'
  return 'grid-cols-2 grid-rows-2'
})

const activeSlotCount = computed(() => hasChampion.value ? challengerSlotCount.value : groupsStore.pkCompareCount)
const hasNextBatch = computed(() => browseOffset.value + activeSlotCount.value < totalPool.value)

const currentRangeLabel = computed(() => {
  if (totalPool.value === 0) return ''
  const start = Math.min(currentOffset.value + 1, totalPool.value)
  const end = Math.min(currentOffset.value + activeSlotCount.value, totalPool.value)
  return `候选 ${start}-${end}/${totalPool.value}`
})

watch(() => groupsStore.currentGroupIndex, () => {
  browseOffset.value = 0
  lightboxPhoto.value = null
})

watch(() => groupsStore.pkCompareCount, () => {
  const slots = activeSlotCount.value
  if (browseOffset.value + slots > totalPool.value) {
    browseOffset.value = Math.max(0, totalPool.value - slots)
  }
})

function goToPrevBatch() {
  browseOffset.value = Math.max(0, browseOffset.value - activeSlotCount.value)
}

function goToNextBatch() {
  browseOffset.value = Math.min(Math.max(0, totalPool.value - activeSlotCount.value), browseOffset.value + activeSlotCount.value)
}

function handleChampionAction(photo: Photo) {
  if (photo.status === 'accepted') {
    groupsStore.removeChampion(photo.id)
  } else if (photo.status !== 'rejected') {
    groupsStore.addChampion(photo.id)
    browseOffset.value = 0
  }
}

function handleRejectAction(photo: Photo) {
  if (photo.status === 'rejected') {
    groupsStore.unrejectPhoto(photo.id)
  } else if (photo.status !== 'accepted') {
    groupsStore.rejectChallenger(photo.id)
  }
}

function openChampionLightbox(photo: Photo) {
  lightboxPhoto.value = photo
}

const lightboxIndex = computed(() => {
  if (!lightboxPhoto.value) return -1
  return champions.value.findIndex(c => c.id === lightboxPhoto.value!.id)
})

function lightboxPrev() {
  if (champions.value.length <= 1) return
  const idx = lightboxIndex.value
  lightboxPhoto.value = champions.value[idx <= 0 ? champions.value.length - 1 : idx - 1]
}

function lightboxNext() {
  if (champions.value.length <= 1) return
  const idx = lightboxIndex.value
  lightboxPhoto.value = champions.value[idx >= champions.value.length - 1 ? 0 : idx + 1]
}

function removeLightboxChampion() {
  if (!lightboxPhoto.value) return
  const idx = lightboxIndex.value
  groupsStore.removeChampion(lightboxPhoto.value.id)
  lightboxPhoto.value = champions.value.length > 0 ? champions.value[Math.min(idx, champions.value.length - 1)] : null
}

function handleReset() {
  groupsStore.resetGroup()
  browseOffset.value = 0
  lightboxPhoto.value = null
}

function goNextGroupFriendly() {
  groupsStore.nextGroup()
}

function exitPK() {
  ui.setViewMode('grid')
}

function handlePKShortcuts(e: KeyboardEvent) {
  const target = e.target as HTMLElement
  if (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.tagName === 'SELECT') return
  if (ui.viewMode !== 'pk') return

  if (lightboxPhoto.value) {
    switch (e.key) {
      case 'ArrowLeft':
        e.preventDefault()
        lightboxPrev()
        break
      case 'ArrowRight':
        e.preventDefault()
        lightboxNext()
        break
      case 'Escape':
        e.preventDefault()
        lightboxPhoto.value = null
        break
    }
    return
  }

  const numKey = parseInt(e.key)
  if (numKey >= 1 && numKey <= 4) {
    const photo = displayPhotos.value[numKey - 1]
    if (photo) {
      e.preventDefault()
      if (e.shiftKey) {
        handleRejectAction(photo)
      } else {
        handleChampionAction(photo)
      }
    }
    return
  }

  switch (e.key) {
    case 'ArrowLeft':
      e.preventDefault()
      if (e.shiftKey) groupsStore.prevGroup()
      else goToPrevBatch()
      break
    case 'ArrowRight':
      e.preventDefault()
      if (e.shiftKey) groupsStore.nextGroup()
      else goToNextBatch()
      break
    case 'Escape':
      e.preventDefault()
      exitPK()
      break
  }
}

onMounted(() => {
  window.addEventListener('keydown', handlePKShortcuts)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handlePKShortcuts)
})
</script>

<style scoped>
.btn-dark {
  display: inline-flex;
  flex-shrink: 0;
  align-items: center;
  gap: 0.375rem;
  border-radius: 0.5rem;
  border: 1px solid rgb(255 255 255 / 0.1);
  padding: 0.375rem 0.75rem;
  font-size: 0.75rem;
  font-weight: 500;
  color: rgb(255 255 255 / 0.7);
  transition: color 0.15s ease, background-color 0.15s ease;
}

.btn-dark:hover:not(:disabled) {
  background: rgb(255 255 255 / 0.1);
  color: white;
}

.btn-dark:disabled {
  opacity: 0.3;
}

.action-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.375rem;
  border-radius: 0.5rem;
  padding: 0.375rem 0.75rem;
  font-size: 0.75rem;
  font-weight: 600;
  transition: color 0.15s ease, background-color 0.15s ease;
}
</style>
