<template>
  <div class="h-screen flex flex-col bg-bg">
    <!-- Header -->
    <header class="h-14 flex items-center justify-between gap-4 px-4 bg-bg-raised border-b border-border shrink-0 shadow-card">
      <div class="flex min-w-0 items-center gap-2">
        <button @click="$router.push('/')" class="btn-icon" title="返回项目列表">
          <ArrowLeft class="h-4 w-4" />
        </button>
        <button @click="ui.toggleSidebar()" class="btn-icon" :title="ui.sidebarVisible ? '隐藏侧栏' : '显示侧栏'">
          <PanelLeftClose v-if="ui.sidebarVisible" class="h-4 w-4" />
          <PanelLeftOpen v-else class="h-4 w-4" />
        </button>
        <div class="min-w-0">
          <div class="truncate text-sm font-semibold text-text-DEFAULT">{{ sessionName }}</div>
          <div class="text-xs text-text-muted">{{ photos.total }} 张照片 · 第 {{ photos.page }}/{{ photos.totalPages }} 页</div>
        </div>
        <button
          @click="$router.push({ name: 'organize', params: { sessionId } })"
          class="ml-2 inline-flex shrink-0 items-center gap-1.5 rounded-lg bg-accent px-3 py-1.5 text-xs font-medium text-white shadow-sm transition-colors hover:bg-accent-hover"
          title="进入照片整理"
        >
          <FolderTree class="h-3.5 w-3.5" />
          整理照片
        </button>
      </div>

      <div class="flex items-center gap-2 overflow-x-auto">
        <!-- View mode tabs -->
        <div class="flex shrink-0 border border-border rounded-lg p-0.5 bg-surface">
          <button
            v-for="m in viewModes"
            :key="m.key"
            @click="ui.setViewMode(m.key)"
            :class="['inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-all', ui.viewMode === m.key ? 'bg-accent text-white shadow-sm' : 'text-text-DEFAULT hover:bg-bg-raised']"
          >
            <component :is="m.icon" class="h-3.5 w-3.5" />
            {{ m.label }}
          </button>
        </div>

        <!-- Grid mode toggle (仅网格视图时显示) -->
        <div v-if="ui.viewMode === 'grid'" class="flex shrink-0 border border-border rounded-lg p-0.5 bg-surface">
          <button
            @click="ui.setGridMode('flat')"
            :class="['px-3 py-1.5 rounded-md text-xs font-medium transition-all', ui.gridMode === 'flat' ? 'bg-accent text-white shadow-sm' : 'text-text-DEFAULT hover:bg-bg-raised']"
          >平铺</button>
          <button
            @click="switchToGrouped()"
            :class="['px-3 py-1.5 rounded-md text-xs font-medium transition-all', ui.gridMode === 'grouped' ? 'bg-accent text-white shadow-sm' : 'text-text-DEFAULT hover:bg-bg-raised']"
          >分组</button>
        </div>

        <!-- 检测相似 -->
        <div class="flex shrink-0 items-center gap-1">
          <button
            @click="detectSimilar"
            :disabled="groupsStore.detecting"
            class="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg border border-border text-text-DEFAULT hover:border-accent hover:text-accent disabled:opacity-50 transition-colors"
            title="检测相似照片"
          >
            <ScanSearch class="h-3.5 w-3.5" />
            {{ groupsStore.detecting ? '检测中...' : '检测相似' }}
          </button>
          <select
            v-model.number="groupsStore.threshold"
            class="h-8 text-xs border border-border rounded-lg px-2 bg-bg-raised text-text-DEFAULT"
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
        <button @click="showAISettings = true" class="btn-icon shrink-0" title="AI 设置">
          <Settings class="h-4 w-4" />
        </button>

        <!-- Export button -->
        <button @click="showExport = true" class="btn-primary inline-flex shrink-0 items-center gap-1.5 text-xs px-3 py-1.5">
          <Download class="h-3.5 w-3.5" />
          导出
        </button>
      </div>
    </header>

    <!-- Main content -->
    <div class="flex-1 flex overflow-hidden">
      <!-- Sidebar -->
      <aside v-if="ui.sidebarVisible" class="w-60 bg-bg-raised border-r border-border overflow-y-auto shrink-0">
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
    <footer class="h-9 flex items-center justify-between px-4 bg-bg-raised border-t border-border shrink-0 text-xs text-text-muted">
      <div class="flex items-center gap-3">
        <span class="text-text-secondary">{{ currentPhoto?.filename || '' }}</span>
      </div>
      <div class="flex items-center gap-3">
        <span>←/→ 翻页</span>
        <span>1-5 评分</span>
        <span>P 入选</span>
        <span>X 淘汰</span>
        <span>S 侧栏</span>
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
import {
  ArrowLeft,
  Columns3,
  Download,
  FolderTree,
  Grid3X3,
  Image,
  PanelLeftClose,
  PanelLeftOpen,
  ScanSearch,
  Settings,
} from 'lucide-vue-next'
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
  { key: 'grid' as const, label: '网格', icon: Grid3X3 },
  { key: 'viewer' as const, label: '浏览', icon: Image },
  { key: 'compare' as const, label: '对比', icon: Columns3 },
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
