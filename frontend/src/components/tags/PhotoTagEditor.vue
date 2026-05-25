<template>
  <div class="space-y-2">
    <div class="text-xs font-medium text-text-secondary">标签</div>

    <!-- 按维度分组显示标签 -->
    <div v-for="dim in groupedTags" :key="dim.dimension" class="space-y-1">
      <span class="text-xs text-text-muted">{{ dimensionLabel(dim.dimension) }}:</span>
      <div class="flex flex-wrap gap-1">
        <span
          v-for="tag in dim.tags"
          :key="tag.id"
          :class="['inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded text-xs',
            tag.source === 'ai' ? 'bg-accent/10 text-accent' : 'bg-blue-50 text-blue-700']"
        >
          {{ tag.tag_value }}
          <button @click="removeTag(tag)" class="opacity-50 hover:opacity-100 ml-0.5">&times;</button>
        </span>
        <!-- 添加按钮 -->
        <button
          @click="startAdding(dim.dimension)"
          class="px-1.5 py-0.5 rounded text-xs border border-dashed border-border text-text-muted hover:border-accent hover:text-accent"
        >+</button>
      </div>
    </div>

    <!-- 空状态 -->
    <div v-if="groupedTags.length === 0" class="text-xs text-text-muted">暂无标签</div>

    <!-- 添加标签弹出 -->
    <div v-if="adding" class="flex items-center gap-1.5 mt-2">
      <select v-model="newDimension" class="text-xs border border-border rounded px-1.5 py-1 bg-white">
        <option value="scene">场景</option>
        <option value="people">人物</option>
        <option value="setting">环境</option>
        <option value="composition">构图</option>
      </select>
      <input
        v-model="newTagValue"
        type="text"
        placeholder="标签名"
        class="text-xs border border-border rounded px-2 py-1 flex-1 bg-white"
        @keydown.enter="confirmAdd"
      />
      <button @click="confirmAdd" class="text-xs text-accent font-medium">添加</button>
      <button @click="adding = false" class="text-xs text-text-muted">取消</button>
    </div>
  </div>
</template>

<script setup lang="ts">
// 照片标签编辑器 - 查看/添加/删除当前照片的标签
import { ref, computed, watch } from 'vue'
import { useTagsStore } from '../../stores/tags'
import type { PhotoTag } from '../../types/photo'

const props = defineProps<{ photoId: string }>()
const tags = useTagsStore()

const adding = ref(false)
const newDimension = ref('scene')
const newTagValue = ref('')

const dimensionLabels: Record<string, string> = {
  scene: '场景',
  people: '人物',
  setting: '环境',
  composition: '构图',
}

function dimensionLabel(dim: string) {
  return dimensionLabels[dim] || dim
}

const groupedTags = computed(() => {
  const dims: Record<string, PhotoTag[]> = {}
  for (const tag of tags.currentPhotoTags) {
    if (!dims[tag.dimension]) dims[tag.dimension] = []
    dims[tag.dimension].push(tag)
  }
  return Object.entries(dims).map(([dimension, tagList]) => ({ dimension, tags: tagList }))
})

function startAdding(dimension: string) {
  newDimension.value = dimension
  newTagValue.value = ''
  adding.value = true
}

async function confirmAdd() {
  if (!newTagValue.value.trim()) return
  await tags.addTag(props.photoId, newDimension.value, newTagValue.value.trim())
  adding.value = false
  newTagValue.value = ''
}

async function removeTag(tag: PhotoTag) {
  await tags.removeTag(props.photoId, tag.id)
}

watch(() => props.photoId, async (id) => {
  if (id) await tags.loadPhotoTags(id)
}, { immediate: true })
</script>
