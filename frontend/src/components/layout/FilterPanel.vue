<template>
  <div class="p-4 space-y-5">
    <div class="text-xs font-semibold text-text-secondary uppercase tracking-wider">筛选</div>

    <!-- Status filter -->
    <div>
      <div class="text-xs text-text-muted mb-2">状态</div>
      <div class="flex flex-wrap gap-1.5">
        <button
          v-for="s in statuses"
          :key="s.value"
          @click="toggleStatus(s.value)"
          :class="['px-3 py-1.5 rounded-lg text-xs font-medium transition-all border', activeStatus === s.value ? 'bg-accent text-white shadow-sm border-accent' : 'bg-bg-raised text-text-secondary border-border hover:text-text-DEFAULT hover:border-text-muted']"
        >{{ s.label }}</button>
      </div>
    </div>

    <!-- Stars filter -->
    <div>
      <div class="text-xs text-text-muted mb-2">最低评分</div>
      <div class="flex gap-1.5">
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
      <div class="text-xs text-text-muted mb-2">列数</div>
      <div class="flex gap-1.5">
        <button
          v-for="n in [2, 3, 4, 5]"
          :key="n"
          @click="ui.setGridColumns(n)"
          :class="['px-3 py-1.5 rounded-lg text-xs font-medium transition-all border', ui.gridColumns === n ? 'bg-accent text-white shadow-sm border-accent' : 'bg-bg-raised text-text-secondary border-border hover:text-text-DEFAULT hover:border-text-muted']"
        >{{ n }}</button>
      </div>
    </div>

    <!-- Reset -->
    <button
      @click="resetFilters"
      class="w-full py-2 text-xs font-medium text-text-secondary hover:text-text-DEFAULT bg-bg-raised border border-border hover:border-text-muted rounded-lg transition-all"
    >重置筛选</button>
  </div>
</template>

<script setup lang="ts">
// 筛选面板 - 按星级、状态、颜色标签组合过滤照片
import { ref } from 'vue'
import { usePhotosStore } from '../../stores/photos'
import { useUIStore } from '../../stores/ui'

const photos = usePhotosStore()
const ui = useUIStore()

const statuses = [
  { value: '', label: '全部' },
  { value: 'pending', label: '待定' },
  { value: 'accepted', label: '入选' },
  { value: 'rejected', label: '淘汰' },
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
  applyAll()
}

function applyAll() {
  photos.setFilters({
    status: activeStatus.value || undefined,
    stars_min: activeStarsMin.value || undefined,
    color_label: activeColor.value || undefined,
  })
  photos.applyFilters()
}
</script>
