<template>
  <div v-if="visible" class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm" @click.self="$emit('close')">
    <div class="bg-white rounded-2xl shadow-elevated w-[500px] max-h-[70vh] flex flex-col">
      <!-- Header -->
      <div class="px-5 py-4 border-b border-border flex items-center justify-between">
        <h3 class="text-base font-semibold text-text-DEFAULT">{{ title }}</h3>
        <button @click="$emit('close')" class="text-text-muted hover:text-text-DEFAULT text-xl leading-none">&times;</button>
      </div>

      <!-- Breadcrumb / current path -->
      <div class="px-5 py-3 border-b border-border-light bg-bg flex items-center gap-1 text-sm overflow-x-auto">
        <button
          @click="navigateTo('')"
          class="text-accent hover:underline shrink-0 font-medium"
        >此电脑</button>
        <template v-for="(seg, idx) in pathSegments" :key="idx">
          <span class="text-text-muted shrink-0">/</span>
          <button
            @click="navigateTo(pathUpTo(idx))"
            class="text-accent hover:underline shrink-0 truncate max-w-[120px]"
          >{{ seg }}</button>
        </template>
      </div>

      <!-- Folder list -->
      <div class="flex-1 overflow-y-auto px-3 py-2 min-h-[200px]">
        <div v-if="loading" class="flex items-center justify-center h-32 text-text-muted text-sm">
          加载中...
        </div>
        <div v-else-if="error" class="flex items-center justify-center h-32 text-red-500 text-sm">
          {{ error }}
        </div>
        <div v-else-if="folders.length === 0" class="flex items-center justify-center h-32 text-text-muted text-sm">
          此目录为空
        </div>
        <div v-else class="space-y-0.5">
          <!-- Parent directory -->
          <button
            v-if="parentPath !== null"
            @click="navigateTo(parentPath!)"
            class="w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm text-text-secondary hover:bg-surface-hover hover:text-text-DEFAULT transition-all text-left"
          >
            <span class="text-base">📁</span>
            <span>..</span>
            <span class="text-text-muted text-xs ml-auto">返回上级</span>
          </button>
          <!-- Folders -->
          <button
            v-for="folder in folders"
            :key="folder"
            @click="enterFolder(folder)"
            class="w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm text-text-DEFAULT hover:bg-surface-hover transition-all text-left"
          >
            <span class="text-base">📁</span>
            <span class="truncate">{{ folder }}</span>
          </button>
        </div>
      </div>

      <!-- Footer -->
      <div class="px-5 py-4 border-t border-border flex items-center justify-between">
        <div class="text-xs text-text-muted truncate max-w-[280px]" :title="currentPath">
          {{ currentPath || '请选择一个文件夹' }}
        </div>
        <div class="flex gap-2">
          <button
            @click="$emit('close')"
            class="px-4 py-2 rounded-lg text-sm font-medium text-text-secondary border border-border hover:text-text-DEFAULT hover:border-text-muted transition-all"
          >取消</button>
          <button
            @click="confirmSelect"
            :disabled="!currentPath"
            class="btn-primary disabled:opacity-40"
          >选择此文件夹</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
// 文件夹选择器 - 可视化浏览文件系统，支持磁盘切换和逐级进入
import { ref, computed, watch } from 'vue'
import { browseFolders } from '../../api/filesystem'

const props = defineProps<{
  visible: boolean
  title: string
  initialPath?: string
}>()

const emit = defineEmits<{
  select: [path: string]
  close: []
}>()

const currentPath = ref('')
const parentPath = ref<string | null>(null)
const folders = ref<string[]>([])
const loading = ref(false)
const error = ref('')

const pathSegments = computed(() => {
  if (!currentPath.value) return []
  const normalized = currentPath.value.replace(/\\/g, '/')
  return normalized.split('/').filter(Boolean)
})

function pathUpTo(index: number): string {
  const segs = pathSegments.value.slice(0, index + 1)
  const joined = segs.join('\\')
  if (/^[A-Z]:$/i.test(segs[0])) {
    return segs.length === 1 ? segs[0] + '\\' : joined
  }
  return '/' + joined
}

async function navigateTo(path: string) {
  loading.value = true
  error.value = ''
  try {
    const res = await browseFolders(path)
    currentPath.value = res.current
    parentPath.value = res.parent
    folders.value = res.folders
  } catch (e: any) {
    error.value = e.response?.data?.detail || '无法访问此路径'
  } finally {
    loading.value = false
  }
}

function enterFolder(folder: string) {
  const sep = currentPath.value.includes('/') ? '/' : '\\'
  const newPath = currentPath.value ? currentPath.value + sep + folder : folder
  navigateTo(newPath)
}

function confirmSelect() {
  if (currentPath.value) {
    emit('select', currentPath.value)
    emit('close')
  }
}

watch(() => props.visible, (v) => {
  if (v) {
    const initial = props.initialPath || ''
    navigateTo(initial)
  }
})
</script>
