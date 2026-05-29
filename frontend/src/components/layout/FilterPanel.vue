<template>
  <div class="p-4 space-y-5">
    <div class="flex items-center justify-between">
      <div class="inline-flex items-center gap-2 text-xs font-semibold text-text-secondary tracking-wider">
        <SlidersHorizontal class="h-4 w-4" />
        筛选
      </div>
      <button
        @click="resetFilters"
        class="text-xs font-medium text-text-muted transition-colors hover:text-accent"
      >重置</button>
    </div>

    <!-- Status filter -->
    <div>
      <div class="text-xs text-text-muted mb-2">状态</div>
      <div class="grid grid-cols-2 gap-1.5">
        <button
          v-for="s in statuses"
          :key="s.value"
          @click="toggleStatus(s.value)"
          :class="['inline-flex items-center justify-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all border', activeStatus === s.value ? 'bg-accent text-white shadow-sm border-accent' : 'bg-bg-raised text-text-secondary border-border hover:text-text-DEFAULT hover:border-accent/40']"
        >
          <component :is="s.icon" class="h-3.5 w-3.5" />
          {{ s.label }}
        </button>
      </div>
    </div>

    <!-- Stars filter -->
    <div>
      <div class="text-xs text-text-muted mb-2">最低评分</div>
      <div class="grid grid-cols-3 gap-1.5">
        <button
          v-for="i in 6"
          :key="i - 1"
          @click="setStarsMin(i - 1)"
          :class="['px-2.5 py-1.5 rounded-lg text-xs font-medium transition-all border', activeStarsMin === (i - 1) ? 'bg-accent text-white shadow-sm border-accent' : 'bg-bg-raised text-text-secondary border-border hover:text-text-DEFAULT hover:border-text-muted']"
        >{{ i - 1 === 0 ? '全部' : (i - 1) + '★' }}</button>
      </div>
    </div>

    <!-- Color filter -->
    <div>
      <div class="text-xs text-text-muted mb-2">色标</div>
      <div class="flex items-center gap-2.5">
        <button
          v-for="c in colors"
          :key="c.value"
          @click="toggleColor(c.value)"
          :class="['w-6 h-6 rounded-full border-2 transition-all', activeColor === c.value ? 'border-text-DEFAULT scale-110 shadow-sm' : 'border-transparent opacity-70 hover:opacity-100 hover:scale-105']"
          :style="{ background: c.hex }"
          :title="c.name"
        ></button>
        <button
          @click="clearColor"
          :class="['px-2 py-0.5 rounded text-xs font-medium transition-colors', !activeColor ? 'text-accent' : 'text-text-muted hover:text-text-DEFAULT']"
        >全部</button>
      </div>
    </div>

    <!-- Divider -->
    <div class="border-t border-border"></div>

    <!-- Grid columns -->
    <div>
      <div class="mb-2 flex items-center justify-between">
        <div class="text-xs text-text-muted">网格列数</div>
        <div class="text-xs font-medium text-text-DEFAULT">{{ ui.gridColumns }} 列</div>
      </div>
      <input
        :value="ui.gridColumns"
        type="range"
        min="2"
        max="8"
        step="1"
        class="w-full accent-accent"
        @input="ui.setGridColumns(parseInt(($event.target as HTMLInputElement).value))"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { CheckCircle2, CircleDashed, SlidersHorizontal, XCircle } from 'lucide-vue-next'
import { usePhotosStore } from '../../stores/photos'
import { useUIStore } from '../../stores/ui'
import { useTagsStore } from '../../stores/tags'

const photos = usePhotosStore()
const ui = useUIStore()
const tags = useTagsStore()

const statuses = [
  { value: '', label: '全部', icon: SlidersHorizontal },
  { value: 'pending', label: '待定', icon: CircleDashed },
  { value: 'accepted', label: '入选', icon: CheckCircle2 },
  { value: 'rejected', label: '淘汰', icon: XCircle },
]

const colors = [
  { value: 'red', hex: '#ef4444', name: '红色' },
  { value: 'yellow', hex: '#eab308', name: '黄色' },
  { value: 'green', hex: '#22c55e', name: '绿色' },
  { value: 'blue', hex: '#3b82f6', name: '蓝色' },
  { value: 'purple', hex: '#a855f7', name: '紫色' },
]

const activeStatus = ref('')
const activeStarsMin = ref(0)
const activeColor = ref('')

function toggleStatus(value: string) {
  activeStatus.value = activeStatus.value === value ? '' : value
  applyAll()
}

function setStarsMin(value: number) {
  activeStarsMin.value = value
  applyAll()
}

function toggleColor(value: string) {
  activeColor.value = activeColor.value === value ? '' : value
  applyAll()
}

function clearColor() {
  activeColor.value = ''
  applyAll()
}

function resetFilters() {
  activeStatus.value = ''
  activeStarsMin.value = 0
  activeColor.value = ''
  tags.clearFilters()
  photos.setFilters({})
  photos.applyFilters()
}

function applyAll() {
  photos.setFilters({
    status: activeStatus.value || undefined,
    stars_min: activeStarsMin.value || undefined,
    color_label: activeColor.value || undefined,
    tag: tags.activeTagFilter,
  })
  photos.applyFilters()
}
</script>
