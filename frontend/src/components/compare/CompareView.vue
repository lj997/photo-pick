<template>
  <div class="h-full flex flex-col bg-neutral-950">
    <!-- Compare toolbar -->
    <div class="h-14 flex items-center justify-between gap-4 px-4 bg-neutral-950/95 border-b border-white/10 shrink-0">
      <div class="flex min-w-0 items-center gap-3">
        <div class="flex h-8 w-8 items-center justify-center rounded-lg bg-white/10 text-white">
          <Columns3 class="h-4 w-4" />
        </div>
        <div class="min-w-0">
          <div class="text-sm font-semibold text-white">对比模式</div>
          <div class="text-xs text-white/45">从当前照片开始并排查看，可直接评分、入选或淘汰</div>
        </div>
      </div>

      <div class="flex items-center gap-2">
        <button
          @click="shiftCompare(-compareCount)"
          :disabled="photos.currentIndex <= 0"
          class="inline-flex items-center gap-1.5 rounded-lg border border-white/10 px-3 py-1.5 text-xs font-medium text-white/70 transition-colors hover:bg-white/10 hover:text-white disabled:opacity-30"
        >
          <ChevronLeft class="h-3.5 w-3.5" />
          上一组
        </button>
        <div class="flex items-center rounded-lg border border-white/10 bg-white/5 p-0.5">
        <button
          v-for="n in [2, 3, 4]"
          :key="n"
          @click="compareCount = n"
          :class="['px-2.5 py-1 rounded-md text-xs font-medium transition-all', compareCount === n ? 'bg-accent text-white shadow-sm' : 'text-white/60 hover:bg-white/10 hover:text-white']"
        >{{ n }} 张</button>
      </div>
        <button
          @click="shiftCompare(compareCount)"
          :disabled="photos.currentIndex >= photos.photos.length - 1"
          class="inline-flex items-center gap-1.5 rounded-lg border border-white/10 px-3 py-1.5 text-xs font-medium text-white/70 transition-colors hover:bg-white/10 hover:text-white disabled:opacity-30"
        >
          下一组
          <ChevronRight class="h-3.5 w-3.5" />
        </button>
      <button
        @click="exitCompare"
          class="inline-flex items-center gap-1.5 rounded-lg bg-white/10 px-3 py-1.5 text-xs font-medium text-white/80 transition-colors hover:bg-white/15 hover:text-white"
      >
          <X class="h-3.5 w-3.5" />
        退出
      </button>
      </div>
    </div>

    <!-- Compare area -->
    <div class="flex-1 min-h-0 grid gap-px bg-white/10 p-px" :class="layoutClass">
      <div
        v-for="(photo, idx) in comparePhotos"
        :key="photo.id"
        class="relative flex min-w-0 min-h-0 flex-col bg-neutral-950"
      >
        <!-- Image container -->
        <button
          class="absolute left-3 top-3 z-10 flex h-7 min-w-7 items-center justify-center rounded-full bg-black/60 px-2 text-xs font-semibold text-white shadow-lg"
          @click="photos.setCurrentIndex(photos.currentIndex + idx)"
          :title="`设为当前照片 ${idx + 1}`"
        >
          {{ idx + 1 }}
        </button>
        <div
          v-if="photo.status !== 'pending'"
          :class="['absolute right-3 top-3 z-10 inline-flex items-center gap-1 rounded-lg px-2 py-1 text-xs font-medium shadow-lg',
            photo.status === 'accepted' ? 'bg-emerald-500 text-white' : 'bg-rose-500 text-white']"
        >
          <Check v-if="photo.status === 'accepted'" class="h-3.5 w-3.5" />
          <X v-else class="h-3.5 w-3.5" />
          {{ photo.status === 'accepted' ? '已入选' : '已淘汰' }}
        </div>
        <div class="flex-1 min-h-0 flex items-center justify-center p-3">
          <img
            :src="getFullPhotoUrl(photo.id)"
            :alt="photo.filename"
            :class="['max-w-full max-h-full object-contain transition-all', photo.status === 'rejected' ? 'opacity-45 grayscale' : '']"
          />
        </div>

        <!-- Photo info bar -->
        <div class="shrink-0 px-3 py-3 bg-neutral-900/95 flex items-center justify-between gap-3 border-t border-white/10">
          <div class="min-w-0">
            <div class="text-white text-xs font-medium truncate">{{ photo.filename }}</div>
            <div class="text-white/45 text-xs mt-0.5">
              <span v-if="photo.aperture">f/{{ photo.aperture }}</span>
              <span v-if="photo.shutter_speed" class="ml-1">{{ photo.shutter_speed }}s</span>
              <span v-if="photo.iso" class="ml-1">ISO {{ photo.iso }}</span>
              <span v-if="photo.focal_length" class="ml-1">{{ photo.focal_length }}mm</span>
            </div>
          </div>
          <div class="flex items-center gap-2 shrink-0">
            <!-- Stars -->
            <div class="flex">
              <button
                v-for="i in 5"
                :key="i"
                @click="photos.setMark(photo.id, { stars: photo.stars === i ? 0 : i })"
                :class="['text-base leading-none transition-colors', i <= photo.stars ? 'text-amber-400' : 'text-white/25 hover:text-amber-300']"
                :title="`${i} 星`"
              >&#9733;</button>
            </div>
            <!-- Pick best -->
            <button
              @click="toggleAccepted(photo)"
              :class="['inline-flex items-center gap-1 rounded-lg px-2.5 py-1.5 text-xs font-medium transition-all',
                photo.status === 'accepted' ? 'bg-emerald-500 text-white' : 'bg-emerald-500/10 text-emerald-200 hover:bg-emerald-500 hover:text-white']"
            >
              <Check class="h-3.5 w-3.5" />
              {{ photo.status === 'accepted' ? '取消入选' : '入选' }}
            </button>
            <button
              @click="toggleRejected(photo)"
              :class="['inline-flex items-center gap-1 rounded-lg px-2.5 py-1.5 text-xs font-medium transition-all',
                photo.status === 'rejected' ? 'bg-rose-500 text-white' : 'bg-rose-500/10 text-rose-200 hover:bg-rose-500 hover:text-white']"
            >
              <X class="h-3.5 w-3.5" />
              {{ photo.status === 'rejected' ? '恢复' : '淘汰' }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <div class="h-9 flex items-center justify-between px-4 bg-neutral-950 border-t border-white/10 text-xs text-white/45">
      <span>{{ photos.currentIndex + 1 }}-{{ Math.min(photos.currentIndex + comparePhotos.length, photos.photos.length) }} / {{ photos.photos.length }}</span>
      <div class="flex items-center gap-3">
        <span>←/→ 切换照片</span>
        <span>C 对比</span>
        <span>Esc 返回浏览</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
// 对比视图 - 左右双图对比，方便在相似照片间做选择
import { ref, computed } from 'vue'
import { Check, ChevronLeft, ChevronRight, Columns3, X } from 'lucide-vue-next'
import { usePhotosStore } from '../../stores/photos'
import { useUIStore } from '../../stores/ui'
import { getFullPhotoUrl } from '../../api/photos'
import type { Photo } from '../../types/photo'

const photos = usePhotosStore()
const ui = useUIStore()

const compareCount = ref(2)

const comparePhotos = computed(() => {
  const current = photos.currentIndex
  const all = photos.photos
  const result = []
  for (let i = current; i < Math.min(current + compareCount.value, all.length); i++) {
    result.push(all[i])
  }
  return result
})

const layoutClass = computed(() => {
  const count = comparePhotos.value.length
  if (count <= 2) return 'grid-cols-2'
  if (count === 3) return 'grid-cols-3'
  return 'grid-cols-2 grid-rows-2'
})

function exitCompare() {
  ui.setViewMode('viewer')
}

function shiftCompare(delta: number) {
  const nextIndex = Math.max(0, Math.min(photos.photos.length - 1, photos.currentIndex + delta))
  photos.setCurrentIndex(nextIndex)
}

function toggleAccepted(photo: Photo) {
  photos.setMark(photo.id, { status: photo.status === 'accepted' ? 'pending' : 'accepted' })
}

function toggleRejected(photo: Photo) {
  photos.setMark(photo.id, { status: photo.status === 'rejected' ? 'pending' : 'rejected' })
}
</script>
