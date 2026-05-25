/**
 * UI 状态管理 - 视图模式、侧边栏、缩放、网格列数、导出弹窗
 */
import { defineStore } from 'pinia'
import { ref } from 'vue'

export type ViewMode = 'grid' | 'viewer' | 'compare' | 'pk'
export type GridMode = 'flat' | 'grouped'

export const useUIStore = defineStore('ui', () => {
  const viewMode = ref<ViewMode>('grid')
  const gridMode = ref<GridMode>('flat')
  const sidebarVisible = ref(true)
  const zoomLevel = ref(1)
  const gridColumns = ref(3)
  const showExportDialog = ref(false)

  function setViewMode(mode: ViewMode) {
    viewMode.value = mode
  }

  function setGridMode(mode: GridMode) {
    gridMode.value = mode
  }

  function toggleSidebar() {
    sidebarVisible.value = !sidebarVisible.value
  }

  function setZoom(level: number) {
    zoomLevel.value = level
  }

  function setGridColumns(cols: number) {
    gridColumns.value = Math.max(2, Math.min(10, cols))
  }

  function toggleExportDialog() {
    showExportDialog.value = !showExportDialog.value
  }

  return {
    viewMode,
    gridMode,
    sidebarVisible,
    zoomLevel,
    gridColumns,
    showExportDialog,
    setViewMode,
    setGridMode,
    toggleSidebar,
    setZoom,
    setGridColumns,
    toggleExportDialog,
  }
})
