<template>
  <div class="h-screen flex flex-col bg-bg">
    <!-- Header -->
    <header class="h-12 flex items-center justify-between px-5 bg-bg-raised border-b border-border shrink-0 shadow-card">
      <div class="flex items-center gap-3">
        <button @click="$router.push('/')" class="btn-ghost px-2 py-1 text-lg">&larr;</button>
        <span class="text-text-DEFAULT font-semibold text-sm">{{ sessionName }}</span>
        <span class="text-text-muted text-xs">{{ photos.total }} 张照片</span>
      </div>

      <div class="flex items-center gap-2">
        <!-- View mode tabs -->
        <div class="flex border border-border rounded-lg p-0.5 bg-bg">
          <button
            v-for="m in viewModes"
            :key="m.key"
            @click="ui.setViewMode(m.key)"
            :class="['px-4 py-1.5 rounded-md text-xs font-medium transition-all', ui.viewMode === m.key ? 'bg-accent text-white shadow-sm' : 'text-text-DEFAULT hover:bg-surface-hover']"
          >{{ m.label }}</button>
        </div>

        <!-- Grid mode toggle (仅网格视图时显示) -->
        <div v-if="ui.viewMode === 'grid'" class="flex border border-border rounded-lg p-0.5 bg-bg ml-1">
          <button
            @click="ui.setGridMode('flat')"
            :class="['px-3 py-1.5 rounded-md text-xs font-medium transition-all', ui.gridMode === 'flat' ? 'bg-accent text-white shadow-sm' : 'text-text-DEFAULT hover:bg-surface-hover']"
          >平铺</button>
          <button
            @click="switchToGrouped()"
            :class="['px-3 py-1.5 rounded-md text-xs font-medium transition-all', ui.gridMode === 'grouped' ? 'bg-accent text-white shadow-sm' : 'text-text-DEFAULT hover:bg-surface-hover']"
          >分组</button>
        </div>

        <!-- 检测相似 -->
        <div class="flex items-center gap-1">
          <button
            @click="detectSimilar"
            :disabled="groupsStore.detecting"
            class="px-3 py-1.5 text-xs font-medium rounded-lg border border-border text-text-DEFAULT hover:bg-surface-hover disabled:opacity-50 transition-colors"
            title="检测相似照片"
          >
            {{ groupsStore.detecting ? '检测中...' : '检测相似' }}
          </button>
          <select
            v-model.number="groupsStore.threshold"
            class="h-7 text-xs border border-border rounded-lg px-1.5 bg-bg text-text-DEFAULT"
            title="相似度精确度（值越小越严格）"
          >
            <option :value="4">高精度</option>
            <option :value="6">较精确</option>
            <option :value="8">标准</option>
            <option :value="12">宽松</option>
            <option :value="16">极宽松</option>
          </select>
        </div>

        <!-- AI Settings button -->
        <button @click="showAISettings = true" class="px-2 py-1.5 text-text-secondary hover:text-accent rounded-lg hover:bg-surface-hover transition-colors" title="AI 设置">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573 1.066c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" /><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /></svg>
        </button>

        <!-- Export button -->
        <button @click="showExport = true" class="btn-primary ml-2 text-xs px-3 py-1.5">
          导出
        </button>
      </div>
    </header>

    <!-- Main content -->
    <div class="flex-1 flex overflow-hidden">
      <!-- Sidebar -->
      <aside v-if="ui.sidebarVisible" class="w-56 bg-bg-raised border-r border-border overflow-y-auto shrink-0">
        <FilterPanel />
        <div class="border-t border-border"></div>
        <TagPanel />
      </aside>

      <!-- Photo area -->
      <main class="flex-1 overflow-hidden bg-bg">
        <PhotoGrid v-if="ui.viewMode === 'grid'" />
        <PhotoViewer v-else-if="ui.viewMode === 'viewer'" />
        <CompareView v-else-if="ui.viewMode === 'compare'" />
        <PKCompareView v-else-if="ui.viewMode === 'pk'" />
      </main>
    </div>

    <!-- Status bar -->
    <footer class="h-8 flex items-center justify-between px-5 bg-bg-raised border-t border-border shrink-0 text-xs text-text-muted">
      <div class="flex items-center gap-3">
        <span>第 {{ photos.page }}/{{ photos.totalPages }} 页</span>
        <span class="text-text-secondary">{{ currentPhoto?.filename || '' }}</span>
      </div>
      <div class="flex items-center gap-4">
        <span>&larr; &rarr; 翻页</span>
        <span>1-5 评分</span>
        <span>P 入选</span>
        <span>X 淘汰</span>
        <span>Ctrl+E 导出</span>
      </div>
    </footer>

    <!-- Export dialog -->
    <ExportDialog :visible="showExport" @close="showExport = false" />

    <!-- AI Settings dialog -->
    <AISettingsDialog :visible="showAISettings" @close="showAISettings = false" />
  </div>
</template>

<script setup lang="ts">
import { computed, ref, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { usePhotosStore } from '../stores/photos'
import { useUIStore } from '../stores/ui'
import { useTagsStore } from '../stores/tags'
import { useGroupsStore } from '../stores/groups'
import { useKeyboard } from '../composables/useKeyboard'
import { useWebSocket } from '../api/websocket'
import PhotoGrid from '../components/grid/PhotoGrid.vue'
import PhotoViewer from '../components/viewer/PhotoViewer.vue'
import CompareView from '../components/compare/CompareView.vue'
import PKCompareView from '../components/compare/PKCompareView.vue'
import FilterPanel from '../components/layout/FilterPanel.vue'
import TagPanel from '../components/tags/TagPanel.vue'
import ExportDialog from '../components/export/ExportDialog.vue'
import AISettingsDialog from '../components/settings/AISettingsDialog.vue'

const route = useRoute()
const photos = usePhotosStore()
const ui = useUIStore()
const tags = useTagsStore()
const groupsStore = useGroupsStore()

useKeyboard()

const sessionId = computed(() => route.params.sessionId as string)
const { on } = useWebSocket(sessionId.value)
const showAISettings = ref(false)

on('thumbnail_ready', (data: { photo_id: string }) => {
  photos.markThumbnailReady(data.photo_id)
})

on('import_complete', () => {
  photos.loadPhotos()
})

on('content_tags_progress', (data: { total: number; processed: number; status?: string }) => {
  tags.setAnalysisProgress(data.total, data.processed)
  if (data.status === 'completed') {
    tags.loadSummary(sessionId.value)
  }
})

on('similarity_progress', (_data: { total: number; processed: number }) => {
  // 可选：显示进度
})

on('similarity_complete', (data: { groups_created: number }) => {
  groupsStore.onDetectionComplete(sessionId.value)
  if (data.groups_created > 0) {
    ui.setGridMode('grouped')
  }
})

onMounted(async () => {
  await photos.loadPhotos(sessionId.value)
})

const viewModes = [
  { key: 'grid' as const, label: '网格' },
  { key: 'viewer' as const, label: '浏览' },
  { key: 'compare' as const, label: '对比' },
]

const showExport = computed({
  get: () => ui.showExportDialog,
  set: (v: boolean) => { ui.showExportDialog = v }
})

const sessionName = computed(() => sessionId.value.slice(0, 8))
const currentPhoto = computed(() => photos.currentPhoto)

function detectSimilar() {
  groupsStore.triggerDetection(sessionId.value)
}

function switchToGrouped() {
  ui.setGridMode('grouped')
  if (groupsStore.groups.length === 0) {
    groupsStore.loadGroups(sessionId.value, 'similar')
  }
}

watch(sessionId, async (newId) => {
  if (newId) await photos.loadPhotos(newId)
})
</script>
