<template>
  <div
    :class="['relative rounded-xl overflow-hidden cursor-pointer ring-2 transition-all group shadow-card hover:shadow-card-hover', selected ? 'ring-accent' : 'ring-transparent']"
    @click.self="$emit('click')"
  >
    <!-- Image with loading state -->
    <div v-if="photo.thumb_sm_ready" class="relative">
      <img
        ref="imgRef"
        :src="thumbnailUrl"
        :alt="photo.filename"
        :class="['w-full h-auto block bg-surface transition-opacity duration-300', imgLoaded ? 'opacity-100' : 'opacity-0']"
        loading="lazy"
        @click="$emit('click')"
        @dblclick="$emit('dblclick')"
        @load="onImgLoad"
        @error="onImgError"
      />
      <!-- Loading placeholder (shows until img onload) -->
      <div v-if="!imgLoaded" class="absolute inset-0 flex flex-col items-center justify-center bg-surface gap-2">
        <div class="w-5 h-5 border-2 border-border border-t-accent rounded-full animate-spin"></div>
        <span class="text-text-muted text-xs">加载中</span>
      </div>
    </div>
    <!-- Thumbnail not yet generated -->
    <div v-else class="w-full aspect-video flex flex-col items-center justify-center bg-surface gap-2">
      <div class="w-5 h-5 border-2 border-border border-t-accent rounded-full animate-spin"></div>
      <span class="text-text-muted text-xs">生成缩略图...</span>
    </div>

    <!-- Hover action overlay (top) - only show when image is ready -->
    <div v-if="photo.thumb_sm_ready && imgLoaded" class="absolute top-0 left-0 right-0 px-2 py-1.5 flex items-center justify-between opacity-0 group-hover:opacity-100 transition-opacity bg-gradient-to-b from-black/50 to-transparent">
      <!-- Color labels -->
      <div class="flex gap-1">
        <button
          v-for="c in colors"
          :key="c.value"
          @click.stop="$emit('mark', { color_label: photo.color_label === c.value ? '' : c.value })"
          :class="['w-4 h-4 rounded-full border transition-transform hover:scale-125', photo.color_label === c.value ? 'border-white scale-110' : 'border-transparent opacity-80 hover:opacity-100']"
          :style="{ background: c.hex }"
          :title="c.name"
        ></button>
      </div>
      <!-- Accept / Reject -->
      <div class="flex gap-1">
        <button
          @click.stop="$emit('mark', { status: photo.status === 'accepted' ? 'pending' : 'accepted' })"
          :class="['w-6 h-6 rounded-md flex items-center justify-center text-sm font-bold transition-colors', photo.status === 'accepted' ? 'bg-green-500 text-white' : 'bg-black/40 text-white/70 hover:bg-green-500 hover:text-white']"
          title="入选 (P)"
        >&#10003;</button>
        <button
          @click.stop="$emit('mark', { status: photo.status === 'rejected' ? 'pending' : 'rejected' })"
          :class="['w-6 h-6 rounded-md flex items-center justify-center text-sm font-bold transition-colors', photo.status === 'rejected' ? 'bg-red-500 text-white' : 'bg-black/40 text-white/70 hover:bg-red-500 hover:text-white']"
          title="淘汰 (X)"
        >&#10005;</button>
      </div>
    </div>

    <!-- Bottom bar: stars + status - only show when image is ready -->
    <div v-if="photo.thumb_sm_ready && imgLoaded" class="absolute bottom-0 left-0 right-0 px-2 py-1.5 flex items-center justify-between bg-gradient-to-t from-black/50 to-transparent">
      <!-- Stars (clickable) -->
      <div class="flex gap-0.5">
        <button
          v-for="i in 5"
          :key="i"
          @click.stop="$emit('mark', { stars: photo.stars === i ? 0 : i })"
          :class="['text-sm leading-none transition-colors hover:text-amber-300', i <= photo.stars ? 'text-amber-400' : 'text-white/40']"
          :title="`${i} 星`"
        >&#9733;</button>
      </div>
      <!-- Status badge -->
      <span v-if="photo.status === 'accepted'" class="text-green-400 text-xs font-bold">&#10003;</span>
      <span v-else-if="photo.status === 'rejected'" class="text-red-400 text-xs font-bold">&#10005;</span>
    </div>

    <!-- Color label indicator (only when loaded) -->
    <div
      v-if="photo.color_label && imgLoaded"
      :class="['absolute top-1.5 right-1.5 w-3 h-3 rounded-full shadow-sm', colorClass]"
    ></div>

    <!-- 入选标识条 -->
    <div
      v-if="photo.status === 'accepted' && imgLoaded"
      class="absolute bottom-0 left-0 right-0 px-2.5 py-1.5 bg-gradient-to-t from-green-600/80 to-green-500/0 flex items-center gap-1"
    >
      <span class="text-white text-xs font-medium">&#10003; 已入选</span>
    </div>

    <!-- Filename on hover -->
    <div v-if="photo.thumb_sm_ready && imgLoaded" class="absolute bottom-8 left-0 right-0 px-2 text-xs text-white/80 truncate opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none">
      {{ photo.filename }}
    </div>
  </div>
</template>

<script setup lang="ts">
// 照片卡片组件 - 缩略图展示、加载动画、悬浮操作栏（评分/标色/入选淘汰）
import { computed, ref, watch, onMounted, nextTick } from 'vue'
import type { Photo } from '../../types/photo'
import { getThumbnailUrl } from '../../api/photos'

const props = defineProps<{
  photo: Photo
  selected: boolean
}>()

defineEmits<{
  click: []
  dblclick: []
  mark: [marks: { stars?: number; color_label?: string; status?: string }]
}>()

const imgRef = ref<HTMLImageElement | null>(null)
const imgLoaded = ref(false)

function onImgLoad() {
  imgLoaded.value = true
}

function onImgError() {
  imgLoaded.value = true
}

function checkComplete() {
  nextTick(() => {
    if (imgRef.value && imgRef.value.complete && imgRef.value.naturalWidth > 0) {
      imgLoaded.value = true
    }
  })
}

onMounted(() => {
  checkComplete()
})

watch(() => props.photo.id, () => {
  imgLoaded.value = false
  nextTick(() => checkComplete())
})

watch(() => props.photo.thumb_sm_ready, (ready) => {
  if (ready) {
    imgLoaded.value = false
    nextTick(() => checkComplete())
  }
})

const thumbnailUrl = computed(() => getThumbnailUrl(props.photo.id, 'lg'))

const colors = [
  { value: 'red', hex: '#ef4444', name: '红色 (6)' },
  { value: 'yellow', hex: '#eab308', name: '黄色 (7)' },
  { value: 'green', hex: '#22c55e', name: '绿色 (8)' },
  { value: 'blue', hex: '#3b82f6', name: '蓝色 (9)' },
  { value: 'purple', hex: '#a855f7', name: '紫色' },
]

const colorClass = computed(() => {
  const map: Record<string, string> = {
    red: 'bg-red-500',
    yellow: 'bg-yellow-400',
    green: 'bg-green-500',
    blue: 'bg-blue-500',
    purple: 'bg-purple-500',
  }
  return map[props.photo.color_label || ''] || ''
})
</script>
