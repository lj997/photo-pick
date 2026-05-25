<template>
  <div class="h-full flex flex-col bg-neutral-900">
    <!-- 工具栏 -->
    <div class="h-12 flex items-center justify-between px-4 bg-black/80 border-b border-white/10 shrink-0">
      <div class="flex items-center gap-3">
        <span class="text-white/90 font-medium text-sm">{{ currentGroup?.name || 'PK 对比' }}</span>
        <span v-if="champions.length" class="text-amber-400 text-xs">{{ champions.length }} 张入选</span>
        <span class="text-white/50 text-xs">{{ totalMembers }} 张照片</span>
        <span v-if="rejectedCount" class="text-red-400/70 text-xs">{{ rejectedCount }} 张已淘汰</span>
      </div>

      <div class="flex items-center gap-3">
        <!-- 同时对比张数 -->
        <div class="flex items-center gap-1">
          <span class="text-white/40 text-xs">同时显示</span>
          <div class="flex border border-white/20 rounded-md overflow-hidden">
            <button
              v-for="n in [2, 3, 4]"
              :key="n"
              @click="groupsStore.pkCompareCount = n"
              :class="['px-2 py-0.5 text-xs transition-colors', groupsStore.pkCompareCount === n ? 'bg-accent text-white' : 'text-white/60 hover:bg-white/10']"
            >{{ n }}</button>
          </div>
        </div>

        <!-- 重置 PK -->
        <button
          @click="handleReset"
          class="px-3 py-1.5 rounded-lg text-xs font-medium bg-white/10 text-orange-300 hover:bg-orange-500/20 hover:text-orange-200 transition-colors"
          title="重置本组 PK 结果"
        >&#8634; 重置</button>

        <!-- 组导航 -->
        <div class="flex items-center gap-1">
          <button
            @click="groupsStore.prevGroup()"
            :disabled="groupsStore.currentGroupIndex <= 0"
            class="px-2 py-1 rounded text-white/60 hover:text-white hover:bg-white/10 disabled:opacity-30 text-sm"
          >&lsaquo;</button>
          <span class="text-white/50 text-xs px-1">
            组 {{ groupsStore.currentGroupIndex + 1 }}/{{ groupsStore.groups.length }}
          </span>
          <button
            @click="groupsStore.nextGroup()"
            :disabled="groupsStore.currentGroupIndex >= groupsStore.groups.length - 1"
            class="px-2 py-1 rounded text-white/60 hover:text-white hover:bg-white/10 disabled:opacity-30 text-sm"
          >&rsaquo;</button>
        </div>

        <button
          @click="exitPK"
          class="px-3 py-1.5 rounded-lg text-xs font-medium bg-white/10 text-white/80 hover:bg-white/20 hover:text-white"
        >退出 (Esc)</button>
      </div>
    </div>

    <!-- 照片并排展示区 -->
    <div class="flex-1 flex overflow-hidden relative">
      <div
        v-for="(photo, idx) in displayPhotos"
        :key="photo.id"
        :class="['flex flex-col', idx < displayPhotos.length - 1 ? 'border-r border-white/10' : '']"
        :style="{ flex: '1 1 0' }"
      >
        <!-- 图片 -->
        <div class="flex-1 flex items-center justify-center p-3 relative">
          <img
            :src="getFullPhotoUrl(photo.id)"
            :alt="photo.filename"
            :class="['max-w-full max-h-full object-contain transition-all', photo.status === 'rejected' ? 'opacity-35 grayscale' : '']"
          />
          <div v-if="photo.status === 'rejected'" class="absolute inset-0 flex items-center justify-center pointer-events-none">
            <span class="text-red-400/50 text-5xl font-bold rotate-[-15deg]">&#10005;</span>
          </div>
          <div v-if="photo.status === 'accepted'" class="absolute top-3 left-3">
            <span class="px-2 py-0.5 rounded text-xs font-medium bg-amber-500/20 text-amber-400 border border-amber-500/30">&#9733; 入选</span>
          </div>
          <!-- 位置编号 -->
          <div class="absolute top-3 right-3">
            <span class="w-6 h-6 rounded-full bg-black/60 text-white/80 text-xs flex items-center justify-center font-mono">{{ idx + 1 }}</span>
          </div>
          <!-- 操作按钮（右下角） -->
          <div class="absolute bottom-3 right-3 flex items-center gap-1.5">
            <template v-if="photo.status === 'rejected'">
              <button @click="handleRejectAction(photo)" class="px-2 py-1 rounded text-xs bg-blue-600 text-white hover:bg-blue-500 shadow-lg" :title="`恢复 [Shift+${idx+1}]`">&#8634; 恢复</button>
            </template>
            <template v-else>
              <button
                v-if="photo.status === 'accepted'"
                @click="handleChampionAction(photo)"
                class="px-2 py-1 rounded text-xs bg-amber-600 text-white hover:bg-amber-500 shadow-lg"
                :title="`取消入选 [${idx+1}]`"
              >&#9733; 取消</button>
              <button
                v-else
                @click="handleChampionAction(photo)"
                class="px-2 py-1 rounded text-xs bg-green-600 text-white hover:bg-green-500 shadow-lg"
                :title="`设为入选 [${idx+1}]`"
              >&#9733; 入选</button>
              <button
                v-if="photo.status !== 'accepted'"
                @click="handleRejectAction(photo)"
                class="px-2 py-1 rounded text-xs bg-red-600 text-white hover:bg-red-500 shadow-lg"
                :title="`淘汰 [Shift+${idx+1}]`"
              >&#10005; 淘汰</button>
            </template>
          </div>
        </div>
        <!-- 信息栏（仅文件名和参数） -->
        <div class="px-3 py-2 bg-black/60 border-t border-white/10">
          <div class="text-white/90 text-xs font-medium truncate">{{ photo.filename }}</div>
          <div class="text-white/50 text-xs mt-0.5">
            <span v-if="photo.aperture">f/{{ photo.aperture }}</span>
            <span v-if="photo.shutter_speed" class="ml-1.5">{{ photo.shutter_speed }}s</span>
            <span v-if="photo.iso" class="ml-1.5">ISO {{ photo.iso }}</span>
          </div>
        </div>
      </div>

      <!-- 无照片占位 -->
      <div v-if="displayPhotos.length === 0" class="flex-1 flex items-center justify-center">
        <span class="text-white/40 text-sm">暂无照片</span>
      </div>

      <!-- 多入选悬浮条（2张及以上时显示） -->
      <div
        v-if="champions.length > 1"
        class="absolute top-0 left-0 right-0 z-10"
      >
        <div class="mx-4 mt-3 rounded-xl bg-black/85 backdrop-blur-sm border border-amber-500/30 shadow-2xl">
          <!-- 标题栏（可折叠） -->
          <div
            class="flex items-center justify-between px-3 py-2 cursor-pointer select-none"
            @click="champBarExpanded = !champBarExpanded"
          >
            <div class="flex items-center gap-2">
              <span class="text-amber-400 text-xs font-medium">&#9733; 入选 ({{ champions.length }})</span>
            </div>
            <span class="text-white/50 text-xs">{{ champBarExpanded ? '收起 &#9650;' : '展开 &#9660;' }}</span>
          </div>
          <!-- 缩略图列表 -->
          <div
            v-show="champBarExpanded"
            class="flex items-center gap-2 px-3 pb-3 overflow-x-auto"
          >
            <div
              v-for="champ in champions"
              :key="champ.id"
              class="relative shrink-0 cursor-pointer group"
              @click="openChampionLightbox(champ)"
            >
              <img
                :src="getThumbnailUrl(champ.id, 'lg')"
                class="h-20 w-auto rounded-lg object-cover border-2 border-amber-500/40 hover:border-amber-400 transition-all"
              />
              <div class="absolute inset-0 rounded-lg bg-black/0 group-hover:bg-black/20 transition-colors flex items-center justify-center">
                <span class="text-white/0 group-hover:text-white/90 text-lg transition-colors">&#128269;</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 入选查看弹窗 -->
    <Teleport to="body">
      <div
        v-if="lightboxPhoto"
        class="fixed inset-0 z-[9999] flex items-center justify-center bg-black/90"
        @click.self="lightboxPhoto = null"
      >
        <!-- 左箭头 -->
        <button
          v-if="champions.length > 1"
          @click="lightboxPrev"
          class="absolute left-4 top-1/2 -translate-y-1/2 w-10 h-10 rounded-full bg-black/60 text-white/80 hover:bg-black/80 hover:text-white flex items-center justify-center text-xl"
        >&lsaquo;</button>

        <div class="relative max-w-[90vw] max-h-[90vh] flex flex-col items-center">
          <img
            :src="getFullPhotoUrl(lightboxPhoto.id)"
            :alt="lightboxPhoto.filename"
            class="max-w-full max-h-[80vh] object-contain rounded-lg"
          />
          <div class="mt-4 flex items-center gap-3">
            <span class="text-white/50 text-xs">{{ lightboxIndex + 1 }} / {{ champions.length }}</span>
            <span class="text-white/80 text-sm">{{ lightboxPhoto.filename }}</span>
            <button
              @click="removeLightboxChampion"
              class="px-3 py-1.5 rounded-lg text-sm bg-red-600 text-white hover:bg-red-500 transition-colors"
            >&#9733; 取消入选</button>
          </div>
          <button
            @click="lightboxPhoto = null"
            class="absolute top-2 right-2 w-8 h-8 rounded-full bg-black/60 text-white/80 hover:bg-black/80 hover:text-white flex items-center justify-center text-lg"
          >&times;</button>
        </div>

        <!-- 右箭头 -->
        <button
          v-if="champions.length > 1"
          @click="lightboxNext"
          class="absolute right-4 top-1/2 -translate-y-1/2 w-10 h-10 rounded-full bg-black/60 text-white/80 hover:bg-black/80 hover:text-white flex items-center justify-center text-xl"
        >&rsaquo;</button>
      </div>
    </Teleport>

    <!-- 底部翻页栏 -->
    <div v-if="totalPool > (hasChampion ? challengerSlotCount : groupsStore.pkCompareCount)" class="h-10 flex items-center justify-center gap-4 bg-black/60 border-t border-white/10 shrink-0">
      <button
        @click="goToPrevBatch"
        :disabled="currentOffset <= 0"
        class="px-3 py-1 rounded text-sm text-white/60 hover:text-white hover:bg-white/10 disabled:opacity-30"
      >&lsaquo; 上一批 (&#8592;)</button>
      <span class="text-white/40 text-xs">
        {{ currentOffset + 1 }}-{{ Math.min(currentOffset + (hasChampion ? challengerSlotCount : groupsStore.pkCompareCount), totalPool) }} / {{ totalPool }}
      </span>
      <button
        @click="goToNextBatch"
        :disabled="currentOffset + (hasChampion ? challengerSlotCount : groupsStore.pkCompareCount) >= totalPool"
        class="px-3 py-1 rounded text-sm text-white/60 hover:text-white hover:bg-white/10 disabled:opacity-30"
      >下一批 (&rarr;) &rsaquo;</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch, onMounted, onUnmounted } from 'vue'
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

const allMembers = computed<Photo[]>(() => {
  return currentGroup.value?.members || []
})

const totalMembers = computed(() => allMembers.value.length)

// 挑战者列表：排除入选
const challengerPool = computed<Photo[]>(() => {
  return allMembers.value.filter(p => !groupsStore.championIds.includes(p.id))
})

// 有入选时翻页基于挑战者列表，无入选时基于全部
const totalPool = computed(() => hasChampion.value ? challengerPool.value.length : allMembers.value.length)
const hasChampion = computed(() => champions.value.length > 0)

// 有入选时，右侧可显示的挑战者槽位数
const challengerSlotCount = computed(() => Math.max(1, groupsStore.pkCompareCount - 1))

const rejectedCount = computed(() => {
  return allMembers.value.filter(m => m.status === 'rejected').length
})

const currentOffset = computed(() => browseOffset.value)

// 有入选：左侧固定入选 + 右侧挑战者；无入选：全部并排
const displayPhotos = computed<Photo[]>(() => {
  if (hasChampion.value && primaryChampion.value) {
    const challengers = challengerPool.value.slice(browseOffset.value, browseOffset.value + challengerSlotCount.value)
    return [primaryChampion.value, ...challengers]
  }
  return allMembers.value.slice(browseOffset.value, browseOffset.value + groupsStore.pkCompareCount)
})

watch(() => groupsStore.currentGroupIndex, () => {
  browseOffset.value = 0
})

watch(() => groupsStore.pkCompareCount, () => {
  const pool = hasChampion.value ? challengerPool.value.length : allMembers.value.length
  const slots = hasChampion.value ? challengerSlotCount.value : groupsStore.pkCompareCount
  if (browseOffset.value + slots > pool) {
    browseOffset.value = Math.max(0, pool - slots)
  }
})

function goToPrevBatch() {
  const slots = hasChampion.value ? challengerSlotCount.value : groupsStore.pkCompareCount
  browseOffset.value = Math.max(0, browseOffset.value - slots)
}

function goToNextBatch() {
  const pool = hasChampion.value ? challengerPool.value.length : allMembers.value.length
  const slots = hasChampion.value ? challengerSlotCount.value : groupsStore.pkCompareCount
  browseOffset.value = Math.min(pool - slots, browseOffset.value + slots)
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
  const prev = idx <= 0 ? champions.value.length - 1 : idx - 1
  lightboxPhoto.value = champions.value[prev]
}

function lightboxNext() {
  if (champions.value.length <= 1) return
  const idx = lightboxIndex.value
  const next = idx >= champions.value.length - 1 ? 0 : idx + 1
  lightboxPhoto.value = champions.value[next]
}

function removeLightboxChampion() {
  if (!lightboxPhoto.value) return
  const idx = lightboxIndex.value
  groupsStore.removeChampion(lightboxPhoto.value.id)
  if (champions.value.length > 0) {
    lightboxPhoto.value = champions.value[Math.min(idx, champions.value.length - 1)]
  } else {
    lightboxPhoto.value = null
  }
}

function handleReset() {
  groupsStore.resetGroup()
  browseOffset.value = 0
}

function exitPK() {
  ui.setViewMode('grid')
}

function handlePKShortcuts(e: KeyboardEvent) {
  const target = e.target as HTMLElement
  if (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA') return
  if (ui.viewMode !== 'pk') return

  // 弹窗打开时，方向键控制弹窗内导航
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

  const photos = displayPhotos.value
  const numKey = parseInt(e.key)

  // 数字键 1-4: 设为入选 / 取消入选
  if (!e.shiftKey && numKey >= 1 && numKey <= 4) {
    const photo = photos[numKey - 1]
    if (photo) {
      e.preventDefault()
      handleChampionAction(photo)
    }
    return
  }

  // Shift + 数字键 1-4: 淘汰 / 恢复
  if (e.shiftKey && numKey >= 1 && numKey <= 4) {
    const photo = photos[numKey - 1]
    if (photo) {
      e.preventDefault()
      handleRejectAction(photo)
    }
    return
  }

  switch (e.key) {
    case 'ArrowLeft':
      e.preventDefault()
      if (e.shiftKey) {
        groupsStore.prevGroup()
      } else {
        goToPrevBatch()
      }
      break
    case 'ArrowRight':
      e.preventDefault()
      if (e.shiftKey) {
        groupsStore.nextGroup()
      } else {
        goToNextBatch()
      }
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
