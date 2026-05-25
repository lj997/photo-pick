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
      </aside>

      <!-- Photo area -->
      <main class="flex-1 overflow-hidden bg-bg">
        <PhotoGrid v-if="ui.viewMode === 'grid'" />
        <PhotoViewer v-else-if="ui.viewMode === 'viewer'" />
        <CompareView v-else-if="ui.viewMode === 'compare'" />
      </main>
    </div>

    <!-- Status bar -->
    <footer class="h-8 flex items-center justify-between px-5 bg-bg-raised border-t border-border shrink-0 text-xs text-text-muted">
      <div class="flex items-center gap-3">
        <span>第 {{ photos.page }}/{{ photos.totalPages }} 页</span>
        <span class="text-text-secondary">{{ currentPhoto?.filename || '' }}</span>
      </div>
      <div class="flex items-center gap-4">
        <span>← → 翻页</span>
        <span>1-5 评分</span>
        <span>P 入选</span>
        <span>X 淘汰</span>
        <span>Ctrl+E 导出</span>
      </div>
    </footer>

    <!-- Export dialog -->
    <ExportDialog :visible="showExport" @close="showExport = false" />
  </div>
</template>

<script setup lang="ts">
// 浏览视图 - 主选片页面，集成网格/查看器/对比三种模式，WebSocket 实时接收缩略图就绪通知
import { computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { usePhotosStore } from '../stores/photos'
import { useUIStore } from '../stores/ui'
import { useKeyboard } from '../composables/useKeyboard'
import { useWebSocket } from '../api/websocket'
import PhotoGrid from '../components/grid/PhotoGrid.vue'
import PhotoViewer from '../components/viewer/PhotoViewer.vue'
import CompareView from '../components/compare/CompareView.vue'
import FilterPanel from '../components/layout/FilterPanel.vue'
import ExportDialog from '../components/export/ExportDialog.vue'

const route = useRoute()
const photos = usePhotosStore()
const ui = useUIStore()

useKeyboard()

const sessionId = computed(() => route.params.sessionId as string)
const { on } = useWebSocket(sessionId.value)

on('thumbnail_ready', (data: { photo_id: string }) => {
  photos.markThumbnailReady(data.photo_id)
})

on('import_complete', () => {
  photos.loadPhotos()
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

watch(sessionId, async (newId) => {
  if (newId) await photos.loadPhotos(newId)
})
</script>
