<template>
  <div class="h-full flex flex-col relative bg-neutral-900">
    <!-- Viewer toolbar -->
    <div class="absolute top-0 left-0 right-0 z-10 flex items-center justify-between px-4 py-3 bg-gradient-to-b from-black/70 to-transparent">
      <!-- Left: photo info -->
      <div v-if="currentPhoto" class="text-sm">
        <div class="text-white font-medium">{{ currentPhoto.filename }}</div>
        <div class="text-white/60 text-xs mt-0.5">
          <span v-if="currentPhoto.aperture">f/{{ currentPhoto.aperture }}</span>
          <span v-if="currentPhoto.shutter_speed" class="ml-2">{{ currentPhoto.shutter_speed }}s</span>
          <span v-if="currentPhoto.iso" class="ml-2">ISO {{ currentPhoto.iso }}</span>
          <span v-if="currentPhoto.focal_length" class="ml-2">{{ currentPhoto.focal_length }}mm</span>
        </div>
      </div>

      <!-- Right: marks controls -->
      <div v-if="currentPhoto" class="flex items-center gap-3">
        <!-- Stars -->
        <div class="flex gap-0.5">
          <button
            v-for="i in 5"
            :key="i"
            @click="photos.setCurrentMark({ stars: currentPhoto!.stars === i ? 0 : i })"
            :class="['text-xl leading-none transition-colors hover:text-amber-300', i <= currentPhoto!.stars ? 'text-amber-400' : 'text-white/30']"
            :title="`${i} 星`"
          >&#9733;</button>
        </div>

        <!-- Color labels -->
        <div class="flex gap-1 ml-2">
          <button
            v-for="c in colors"
            :key="c.value"
            @click="photos.setCurrentMark({ color_label: currentPhoto!.color_label === c.value ? '' : c.value })"
            :class="['w-5 h-5 rounded-full border-2 transition-transform hover:scale-125', currentPhoto!.color_label === c.value ? 'border-white scale-110' : 'border-transparent opacity-70 hover:opacity-100']"
            :style="{ background: c.hex }"
            :title="c.name"
          ></button>
        </div>

        <!-- Accept / Reject -->
        <div class="flex gap-1 ml-2">
          <button
            @click="photos.setCurrentMark({ status: currentPhoto!.status === 'accepted' ? 'pending' : 'accepted' })"
            :class="['px-3 py-1 rounded-md text-sm font-medium transition-colors', currentPhoto!.status === 'accepted' ? 'bg-green-500 text-white' : 'bg-white/10 text-white/70 hover:bg-green-500 hover:text-white']"
            title="入选 (P)"
          >&#10003; 入选</button>
          <button
            @click="photos.setCurrentMark({ status: currentPhoto!.status === 'rejected' ? 'pending' : 'rejected' })"
            :class="['px-3 py-1 rounded-md text-sm font-medium transition-colors', currentPhoto!.status === 'rejected' ? 'bg-red-500 text-white' : 'bg-white/10 text-white/70 hover:bg-red-500 hover:text-white']"
            title="淘汰 (X)"
          >&#10005; 淘汰</button>
        </div>
      </div>
    </div>

    <!-- Image area -->
    <div
      class="flex-1 flex items-center justify-center overflow-hidden w-full relative"
      @wheel="onWheel"
      @mousedown="startPan"
      @mousemove="onPan"
      @mouseup="endPan"
      @mouseleave="endPan"
    >
      <!-- Prev button -->
      <button
        v-if="photos.currentIndex > 0 || photos.page > 1"
        @click="photos.prev()"
        class="absolute left-3 top-1/2 -translate-y-1/2 z-10 w-10 h-16 flex items-center justify-center rounded-lg bg-black/30 text-white/70 hover:bg-black/60 hover:text-white transition-colors text-2xl"
        title="上一张 (←)"
      >&#8249;</button>

      <img
        v-if="currentPhoto"
        :src="imageUrl"
        :alt="currentPhoto.filename"
        :style="imageStyle"
        :class="['select-none', zoom <= 1 ? 'max-w-full max-h-full object-contain' : 'max-w-none']"
        draggable="false"
        @load="onImageLoad"
        @dblclick="toggleZoom"
      />

      <!-- Next button -->
      <button
        v-if="photos.currentIndex < photos.photos.length - 1 || photos.page < photos.totalPages"
        @click="photos.next()"
        class="absolute right-3 top-1/2 -translate-y-1/2 z-10 w-10 h-16 flex items-center justify-center rounded-lg bg-black/30 text-white/70 hover:bg-black/60 hover:text-white transition-colors text-2xl"
        title="下一张 (→)"
      >&#8250;</button>
    </div>

    <!-- Bottom bar: zoom controls + nav info -->
    <div class="absolute bottom-0 left-0 right-0 z-10 flex items-center justify-between px-4 py-3 bg-gradient-to-t from-black/70 to-transparent">
      <!-- Zoom controls -->
      <div class="flex items-center gap-2">
        <button
          @click="setZoomLevel(Math.max(0.5, zoom - 0.5))"
          class="w-7 h-7 flex items-center justify-center rounded-md bg-white/10 text-white/70 hover:bg-white/20 hover:text-white text-lg"
          title="缩小"
        >-</button>
        <button
          @click="toggleZoom()"
          class="px-2.5 py-0.5 rounded-md bg-white/10 text-white/70 hover:bg-white/20 hover:text-white text-xs min-w-[50px] text-center font-medium"
          title="切换适配/100%"
        >{{ Math.round(zoom * 100) }}%</button>
        <button
          @click="setZoomLevel(Math.min(5, zoom + 0.5))"
          class="w-7 h-7 flex items-center justify-center rounded-md bg-white/10 text-white/70 hover:bg-white/20 hover:text-white text-lg"
          title="放大"
        >+</button>
        <button
          @click="setZoomLevel(1)"
          class="px-2.5 py-0.5 rounded-md bg-white/10 text-white/70 hover:bg-white/20 hover:text-white text-xs ml-1 font-medium"
          title="适配屏幕"
        >适配</button>
        <button
          @click="setZoomLevel(2)"
          class="px-2.5 py-0.5 rounded-md bg-white/10 text-white/70 hover:bg-white/20 hover:text-white text-xs font-medium"
          title="100%原始尺寸"
        >原始</button>
      </div>

      <!-- Navigation info -->
      <div class="text-white/60 text-xs">
        {{ (photos.page - 1) * photos.pageSize + photos.currentIndex + 1 }} / {{ photos.total }}
      </div>

      <!-- View mode buttons -->
      <div class="flex items-center gap-1">
        <button
          @click="ui.setViewMode('grid')"
          class="px-2.5 py-1 rounded-md text-xs font-medium bg-white/10 text-white/70 hover:bg-white/20 hover:text-white"
          title="网格视图 (G)"
        >网格</button>
        <button
          @click="ui.setViewMode('compare')"
          class="px-2.5 py-1 rounded-md text-xs font-medium bg-white/10 text-white/70 hover:bg-white/20 hover:text-white"
          title="对比模式 (C)"
        >对比</button>
      </div>
    </div>

    <!-- 右侧标签面板 -->
    <div v-if="currentPhoto" class="absolute top-14 right-3 z-10 w-52 bg-white/95 rounded-xl shadow-elevated p-3 backdrop-blur-sm">
      <PhotoTagEditor :photo-id="currentPhoto.id" />
    </div>
  </div>
</template>

<script setup lang="ts">
// 照片查看器 - 单张大图浏览，支持缩放、EXIF 信息展示、评分操作
import { ref, computed, watch } from 'vue'
import { usePhotosStore } from '../../stores/photos'
import { useUIStore } from '../../stores/ui'
import { getFullPhotoUrl } from '../../api/photos'
import PhotoTagEditor from '../tags/PhotoTagEditor.vue'

const photos = usePhotosStore()
const ui = useUIStore()

const zoom = ref(1)
const panX = ref(0)
const panY = ref(0)
const isPanning = ref(false)
const panStart = ref({ x: 0, y: 0 })
const naturalWidth = ref(0)
const naturalHeight = ref(0)

const currentPhoto = computed(() => photos.currentPhoto)

const colors = [
  { value: 'red', hex: '#ef4444', name: '红色 (6)' },
  { value: 'yellow', hex: '#eab308', name: '黄色 (7)' },
  { value: 'green', hex: '#22c55e', name: '绿色 (8)' },
  { value: 'blue', hex: '#3b82f6', name: '蓝色 (9)' },
  { value: 'purple', hex: '#a855f7', name: '紫色' },
]

const imageUrl = computed(() => {
  if (!currentPhoto.value) return ''
  return getFullPhotoUrl(currentPhoto.value.id)
})

const imageStyle = computed(() => ({
  transform: zoom.value > 1 ? `scale(${zoom.value}) translate(${panX.value}px, ${panY.value}px)` : undefined,
  transition: isPanning.value ? 'none' : 'transform 0.2s ease',
  cursor: zoom.value > 1 ? (isPanning.value ? 'grabbing' : 'grab') : 'zoom-in',
}))

function setZoomLevel(level: number) {
  zoom.value = level
  if (level <= 1) {
    panX.value = 0
    panY.value = 0
  }
  ui.setZoom(level)
}

function toggleZoom() {
  if (zoom.value <= 1) {
    setZoomLevel(2)
  } else {
    setZoomLevel(1)
  }
}

function onWheel(e: WheelEvent) {
  e.preventDefault()
  const delta = e.deltaY > 0 ? -0.25 : 0.25
  const newZoom = Math.max(0.5, Math.min(5, zoom.value + delta))
  setZoomLevel(newZoom)
}

function startPan(e: MouseEvent) {
  if (zoom.value <= 1) return
  isPanning.value = true
  panStart.value = { x: e.clientX - panX.value, y: e.clientY - panY.value }
}

function onPan(e: MouseEvent) {
  if (!isPanning.value) return
  panX.value = e.clientX - panStart.value.x
  panY.value = e.clientY - panStart.value.y
}

function endPan() {
  isPanning.value = false
}

function onImageLoad(e: Event) {
  const img = e.target as HTMLImageElement
  naturalWidth.value = img.naturalWidth
  naturalHeight.value = img.naturalHeight
}

watch(currentPhoto, () => {
  zoom.value = 1
  panX.value = 0
  panY.value = 0
})

watch(() => ui.zoomLevel, (newZoom) => {
  if (newZoom !== zoom.value) {
    zoom.value = newZoom
    if (newZoom <= 1) {
      panX.value = 0
      panY.value = 0
    }
  }
})
</script>
