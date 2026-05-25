<template>
  <div class="p-4 space-y-4">
    <!-- 标题区 -->
    <div class="flex items-center justify-between">
      <span class="text-xs font-semibold text-text-secondary tracking-wider">智能标签</span>
      <button
        @click="startAnalysis"
        :disabled="tags.analyzing || !aiEnabled"
        :class="['text-xs px-2.5 py-1 rounded-lg font-medium transition-colors',
          tags.analyzing ? 'bg-surface text-text-muted cursor-not-allowed' :
          !aiEnabled ? 'bg-surface text-text-muted cursor-not-allowed' :
          'bg-accent/10 text-accent hover:bg-accent/20']"
      >
        {{ tags.analyzing ? '分析中...' : 'AI 分析' }}
      </button>
    </div>

    <!-- AI 未启用提示 -->
    <div v-if="!aiEnabled" class="text-xs text-text-muted py-2">
      AI 功能未启用，请先在设置中配置
    </div>

    <!-- 分析进度 -->
    <div v-if="tags.analyzing" class="space-y-1">
      <div class="h-1.5 bg-surface rounded-full overflow-hidden">
        <div class="h-full bg-accent transition-all rounded-full" :style="{ width: progressPercent + '%' }"></div>
      </div>
      <span class="text-xs text-text-muted">{{ tags.analysisProgress.processed }} / {{ tags.analysisProgress.total }}</span>
    </div>

    <!-- 无标签提示 -->
    <div v-if="!tags.analyzing && tags.tagSummary.dimensions.length === 0 && aiEnabled" class="text-xs text-text-muted py-2">
      暂无标签数据，点击"AI 分析"开始
    </div>

    <!-- 标签维度列表 -->
    <div v-for="dim in tags.tagSummary.dimensions" :key="dim.dimension" class="space-y-1.5">
      <div class="text-xs font-medium text-text-secondary">{{ dimensionLabel(dim.dimension) }}</div>
      <div class="flex flex-wrap gap-1.5">
        <button
          v-for="tag in dim.tags"
          :key="tag.value"
          @click="toggleTag(dim.dimension, tag.value)"
          :class="['px-2 py-0.5 rounded-md text-xs transition-colors border',
            isActive(dim.dimension, tag.value)
              ? 'bg-accent text-white border-accent'
              : 'bg-surface border-border text-text-DEFAULT hover:border-accent/50']"
        >
          {{ tag.value }}
          <span class="ml-0.5 opacity-70">{{ tag.count }}</span>
        </button>
      </div>
    </div>

    <!-- 清除筛选 -->
    <button
      v-if="tags.activeFilters.length > 0"
      @click="tags.clearFilters(); onFilterChange()"
      class="text-xs text-accent hover:text-accent-hover"
    >
      清除标签筛选
    </button>
  </div>
</template>

<script setup lang="ts">
// 智能标签面板 - 展示标签统计，点击标签筛选照片
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useTagsStore } from '../../stores/tags'
import { usePhotosStore } from '../../stores/photos'
import { getAISettings, startContentAnalysis } from '../../api/aiSettings'

const route = useRoute()
const tags = useTagsStore()
const photos = usePhotosStore()

const aiEnabled = ref(false)
const sessionId = computed(() => route.params.sessionId as string)

const progressPercent = computed(() => {
  if (tags.analysisProgress.total === 0) return 0
  return Math.round((tags.analysisProgress.processed / tags.analysisProgress.total) * 100)
})

const dimensionLabels: Record<string, string> = {
  scene: '场景/主题',
  people: '人物',
  setting: '环境',
  composition: '构图',
}

function dimensionLabel(dim: string) {
  return dimensionLabels[dim] || dim
}

function isActive(dimension: string, value: string) {
  return tags.activeFilters.some(f => f.dimension === dimension && f.value === value)
}

function toggleTag(dimension: string, value: string) {
  tags.toggleFilter(dimension, value)
  onFilterChange()
}

function onFilterChange() {
  photos.filters.tag = tags.activeTagFilter
  photos.applyFilters()
}

async function startAnalysis() {
  if (!sessionId.value || tags.analyzing) return
  tags.analyzing = true
  tags.analysisProgress = { total: 0, processed: 0 }
  try {
    await startContentAnalysis(sessionId.value)
  } catch {
    tags.analyzing = false
  }
}

onMounted(async () => {
  try {
    const settings = await getAISettings()
    aiEnabled.value = settings.ai_enabled
  } catch {}
  if (sessionId.value) {
    await tags.loadSummary(sessionId.value)
  }
})

watch(sessionId, async (id) => {
  if (id) await tags.loadSummary(id)
})
</script>
