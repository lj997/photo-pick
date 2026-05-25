/**
 * 标签状态管理 - 标签统计、激活筛选、当前照片标签
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { TagSummary, PhotoTag } from '../types/photo'
import { getSessionTagSummary, getPhotoTags, addPhotoTag, deletePhotoTag } from '../api/tags'

export const useTagsStore = defineStore('tags', () => {
  const tagSummary = ref<TagSummary>({ dimensions: [] })
  const activeFilters = ref<{ dimension: string; value: string }[]>([])
  const currentPhotoTags = ref<PhotoTag[]>([])
  const loading = ref(false)
  const analyzing = ref(false)
  const analysisProgress = ref({ total: 0, processed: 0 })

  const activeTagFilter = computed(() => {
    if (activeFilters.value.length === 0) return undefined
    const f = activeFilters.value[0]
    return `${f.dimension}:${f.value}`
  })

  async function loadSummary(sessionId: string) {
    loading.value = true
    try {
      tagSummary.value = await getSessionTagSummary(sessionId)
    } finally {
      loading.value = false
    }
  }

  function toggleFilter(dimension: string, value: string) {
    const idx = activeFilters.value.findIndex(
      f => f.dimension === dimension && f.value === value
    )
    if (idx >= 0) {
      activeFilters.value.splice(idx, 1)
    } else {
      activeFilters.value = [{ dimension, value }]
    }
  }

  function clearFilters() {
    activeFilters.value = []
  }

  async function loadPhotoTags(photoId: string) {
    currentPhotoTags.value = await getPhotoTags(photoId)
  }

  async function addTag(photoId: string, dimension: string, tagValue: string) {
    const tag = await addPhotoTag(photoId, dimension, tagValue)
    currentPhotoTags.value.push(tag)
  }

  async function removeTag(photoId: string, tagId: string) {
    await deletePhotoTag(photoId, tagId)
    currentPhotoTags.value = currentPhotoTags.value.filter(t => t.id !== tagId)
  }

  function setAnalysisProgress(total: number, processed: number) {
    analysisProgress.value = { total, processed }
    if (processed >= total) {
      analyzing.value = false
    }
  }

  return {
    tagSummary,
    activeFilters,
    activeTagFilter,
    currentPhotoTags,
    loading,
    analyzing,
    analysisProgress,
    loadSummary,
    toggleFilter,
    clearFilters,
    loadPhotoTags,
    addTag,
    removeTag,
    setAnalysisProgress,
  }
})
