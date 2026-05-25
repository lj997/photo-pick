<template>
  <div class="h-full flex flex-col">
    <!-- Compare toolbar -->
    <div class="h-11 flex items-center gap-4 px-5 bg-bg-raised border-b border-border shrink-0">
      <span class="text-sm font-medium text-text-DEFAULT">对比模式</span>
      <div class="flex items-center gap-1 ml-4">
        <button
          v-for="n in [2, 3, 4]"
          :key="n"
          @click="compareCount = n"
          :class="['px-2.5 py-1 rounded-lg text-xs font-medium transition-all border', compareCount === n ? 'bg-accent text-white shadow-sm border-accent' : 'bg-bg-raised text-text-secondary border-border hover:text-text-DEFAULT hover:border-text-muted']"
        >{{ n }} 张</button>
      </div>
      <button
        @click="exitCompare"
        class="ml-auto px-3 py-1 text-sm font-medium text-text-secondary border border-border hover:text-text-DEFAULT hover:border-text-muted rounded-lg transition-all"
      >
        退出对比 (Esc)
      </button>
    </div>

    <!-- Compare area -->
    <div class="flex-1 min-h-0 flex" :class="layoutClass">
      <div
        v-for="photo in comparePhotos"
        :key="photo.id"
        class="relative flex flex-col min-w-0 min-h-0 border border-border"
        :class="paneClass"
      >
        <!-- Image container -->
        <div class="flex-1 min-h-0 flex items-center justify-center bg-neutral-900 p-1">
          <img
            :src="getFullPhotoUrl(photo.id)"
            :alt="photo.filename"
            class="max-w-full max-h-full object-contain"
          />
        </div>

        <!-- Photo info bar -->
        <div class="shrink-0 px-3 py-2 bg-bg-raised flex items-center justify-between gap-2 border-t border-border">
          <div class="min-w-0">
            <div class="text-text-DEFAULT text-xs font-medium truncate">{{ photo.filename }}</div>
            <div class="text-text-muted text-xs mt-0.5">
              <span v-if="photo.aperture">f/{{ photo.aperture }}</span>
              <span v-if="photo.shutter_speed" class="ml-1">{{ photo.shutter_speed }}s</span>
              <span v-if="photo.iso" class="ml-1">ISO {{ photo.iso }}</span>
            </div>
          </div>
          <div class="flex items-center gap-1 shrink-0">
            <!-- Stars -->
            <div class="flex">
              <button
                v-for="i in 5"
                :key="i"
                @click="photos.setMark(photo.id, { stars: photo.stars === i ? 0 : i })"
                :class="['text-sm leading-none', i <= photo.stars ? 'text-amber-500' : 'text-text-muted hover:text-amber-400']"
              >&#9733;</button>
            </div>
            <!-- Pick best -->
            <button
              @click="photos.setMark(photo.id, { status: 'accepted' })"
              :class="['ml-2 px-2 py-0.5 rounded-md text-xs font-medium transition-all', photo.status === 'accepted' ? 'bg-green-500 text-white' : 'bg-green-50 text-green-700 hover:bg-green-500 hover:text-white']"
            >
              {{ photo.status === 'accepted' ? '&#10003; 最佳' : '选中' }}
            </button>
            <button
              @click="photos.setMark(photo.id, { status: 'rejected' })"
              :class="['px-2 py-0.5 rounded-md text-xs font-medium transition-all', photo.status === 'rejected' ? 'bg-red-500 text-white' : 'bg-red-50 text-red-700 hover:bg-red-500 hover:text-white']"
            >&#10005;</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
// 对比视图 - 左右双图对比，方便在相似照片间做选择
import { ref, computed } from 'vue'
import { usePhotosStore } from '../../stores/photos'
import { useUIStore } from '../../stores/ui'
import { getFullPhotoUrl } from '../../api/photos'

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
  if (count <= 2) return 'flex-row'
  return 'flex-wrap'
})

const paneClass = computed(() => {
  const count = comparePhotos.value.length
  if (count <= 2) return 'flex-1'
  return 'w-1/2 h-1/2'
})

function exitCompare() {
  ui.setViewMode('viewer')
}
</script>
