/**
 * 键盘快捷键 - 方向键翻照片、数字键评分/标色、字母键切换状态和视图模式
 */
import { onMounted, onUnmounted } from 'vue'
import { usePhotosStore } from '../stores/photos'
import { useUIStore } from '../stores/ui'

export function useKeyboard() {
  const photos = usePhotosStore()
  const ui = useUIStore()

  function handleKeydown(e: KeyboardEvent) {
    const target = e.target as HTMLElement
    if (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA') return

    // PK 模式快捷键由 PKCompareView 组件自行处理
    if (ui.viewMode === 'pk') return

    switch (e.key) {
      case 'ArrowRight':
      case 'j':
        e.preventDefault()
        photos.next()
        break
      case 'ArrowLeft':
      case 'k':
        e.preventDefault()
        photos.prev()
        break
      case '1':
      case '2':
      case '3':
      case '4':
      case '5':
        e.preventDefault()
        photos.setCurrentMark({ stars: parseInt(e.key) })
        break
      case '0':
        e.preventDefault()
        photos.setCurrentMark({ stars: 0 })
        break
      case '6':
        e.preventDefault()
        photos.setCurrentMark({ color_label: 'red' })
        break
      case '7':
        e.preventDefault()
        photos.setCurrentMark({ color_label: 'yellow' })
        break
      case '8':
        e.preventDefault()
        photos.setCurrentMark({ color_label: 'green' })
        break
      case '9':
        e.preventDefault()
        photos.setCurrentMark({ color_label: 'blue' })
        break
      case 'p':
        e.preventDefault()
        photos.setCurrentMark({ status: 'accepted' })
        break
      case 'x':
        e.preventDefault()
        photos.setCurrentMark({ status: 'rejected' })
        break
      case 'u':
        e.preventDefault()
        photos.setCurrentMark({ status: 'pending' })
        break
      case ' ':
      case 'z':
        e.preventDefault()
        if (ui.viewMode === 'viewer') {
          ui.setZoom(ui.zoomLevel === 1 ? 2 : 1)
        }
        break
      case 'Enter':
        e.preventDefault()
        if (ui.viewMode === 'grid') {
          ui.setViewMode('viewer')
        }
        break
      case 'g':
        e.preventDefault()
        ui.setViewMode('grid')
        break
      case 'Escape':
        e.preventDefault()
        if (ui.viewMode === 'compare') {
          ui.setViewMode('viewer')
        } else if (ui.viewMode === 'viewer') {
          ui.setViewMode('grid')
        }
        break
      case 'f':
        e.preventDefault()
        if (ui.viewMode === 'grid') {
          ui.setViewMode('viewer')
        }
        break
      case 'PageDown':
        e.preventDefault()
        photos.nextPage()
        break
      case 'PageUp':
        e.preventDefault()
        photos.prevPage()
        break
      case 'e':
        if (e.ctrlKey || e.metaKey) {
          e.preventDefault()
          ui.toggleExportDialog()
        }
        break
      case 'c':
        if (!e.ctrlKey && !e.metaKey) {
          e.preventDefault()
          ui.setViewMode('compare')
        }
        break
    }
  }

  onMounted(() => {
    window.addEventListener('keydown', handleKeydown)
  })

  onUnmounted(() => {
    window.removeEventListener('keydown', handleKeydown)
  })
}
