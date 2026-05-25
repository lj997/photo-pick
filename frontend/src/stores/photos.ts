/**
 * 照片状态管理 - 分页加载、当前选中、筛选、评分标记、缩略图就绪通知
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Photo, MarkUpdate } from '../types/photo'
import { listPhotos, updateMarks, type PhotoListParams } from '../api/photos'

export const usePhotosStore = defineStore('photos', () => {
  const photos = ref<Photo[]>([])
  const total = ref(0)
  const currentIndex = ref(0)
  const loading = ref(false)
  const sessionId = ref('')

  // Pagination
  const page = ref(1)
  const pageSize = ref(50)
  const totalPages = computed(() => Math.ceil(total.value / pageSize.value))

  const currentPhoto = computed(() => photos.value[currentIndex.value] || null)

  const filters = ref<{
    stars_min?: number
    stars_max?: number
    status?: string
    color_label?: string
  }>({})

  async function loadPhotos(sid?: string) {
    if (sid) sessionId.value = sid
    loading.value = true
    try {
      const params: PhotoListParams = {
        ...filters.value,
        offset: (page.value - 1) * pageSize.value,
        limit: pageSize.value,
      }
      const result = await listPhotos(sessionId.value, params)
      photos.value = result.photos
      total.value = result.total
    } finally {
      loading.value = false
    }
  }

  async function goToPage(p: number) {
    if (p < 1 || p > totalPages.value) return
    page.value = p
    currentIndex.value = 0
    await loadPhotos()
  }

  async function nextPage() {
    await goToPage(page.value + 1)
  }

  async function prevPage() {
    await goToPage(page.value - 1)
  }

  function setPageSize(size: number) {
    pageSize.value = size
    page.value = 1
    loadPhotos()
  }

  function setCurrentIndex(index: number) {
    if (index >= 0 && index < photos.value.length) {
      currentIndex.value = index
    }
  }

  function next() {
    if (currentIndex.value < photos.value.length - 1) {
      currentIndex.value++
    } else if (page.value < totalPages.value) {
      nextPage()
    }
  }

  function prev() {
    if (currentIndex.value > 0) {
      currentIndex.value--
    } else if (page.value > 1) {
      prevPage().then(() => {
        currentIndex.value = photos.value.length - 1
      })
    }
  }

  async function setMark(photoId: string, mark: MarkUpdate) {
    const updated = await updateMarks(photoId, mark)
    const idx = photos.value.findIndex(p => p.id === photoId)
    if (idx !== -1) {
      photos.value[idx] = updated
    }
  }

  async function setCurrentMark(mark: MarkUpdate) {
    const photo = currentPhoto.value
    if (photo) {
      await setMark(photo.id, mark)
    }
  }

  function setFilters(newFilters: typeof filters.value) {
    filters.value = newFilters
  }

  function markThumbnailReady(photoId: string) {
    const idx = photos.value.findIndex(p => p.id === photoId)
    if (idx !== -1) {
      photos.value[idx] = { ...photos.value[idx], thumb_sm_ready: true, thumb_lg_ready: true }
    }
  }

  async function applyFilters() {
    page.value = 1
    currentIndex.value = 0
    await loadPhotos()
  }

  return {
    photos,
    total,
    currentIndex,
    currentPhoto,
    loading,
    filters,
    page,
    pageSize,
    totalPages,
    loadPhotos,
    goToPage,
    nextPage,
    prevPage,
    setPageSize,
    setCurrentIndex,
    next,
    prev,
    setMark,
    setCurrentMark,
    setFilters,
    markThumbnailReady,
    applyFilters,
  }
})
