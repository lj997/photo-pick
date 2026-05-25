<template>
  <div class="h-screen flex flex-col items-center justify-center bg-bg p-8">
    <div class="w-full max-w-lg">
      <!-- Logo & title -->
      <div class="text-center mb-10">
        <h1 class="text-3xl font-bold text-text-DEFAULT tracking-tight">光影甄选</h1>
        <p class="text-text-secondary mt-2">专业选片工具 · 快速浏览 · 智能标记 · 高效导出</p>
      </div>

      <!-- Import card -->
      <div class="bg-bg-raised rounded-xl shadow-card p-6 mb-6">
        <label class="block text-sm font-medium text-text-DEFAULT mb-2">导入照片文件夹</label>
        <div class="flex gap-2">
          <input
            v-model="folderPath"
            type="text"
            placeholder="输入文件夹路径，例如 E:\Photos\2024"
            class="input-base flex-1"
            @keyup.enter="importFolder"
          />
          <button
            @click="showPicker = true"
            class="px-3 py-2 rounded-lg text-sm font-medium border border-border text-text-DEFAULT hover:border-text-muted transition-all whitespace-nowrap"
          >浏览</button>
          <button
            @click="importFolder"
            :disabled="importing"
            class="btn-primary whitespace-nowrap"
          >
            {{ importing ? '导入中...' : '开始导入' }}
          </button>
        </div>
        <p v-if="error" class="mt-3 text-red-600 text-sm">{{ error }}</p>
        <p v-if="importProgress" class="mt-3 text-text-secondary text-sm">{{ importProgress }}</p>
      </div>

      <!-- Recent sessions -->
      <div v-if="sessions.length">
        <h2 class="text-sm font-medium text-text-secondary mb-3 px-1">最近的项目</h2>
        <div class="space-y-2">
          <div
            v-for="session in sessions"
            :key="session.id"
            class="flex items-center justify-between px-4 py-3 bg-bg-raised rounded-xl shadow-card hover:shadow-card-hover cursor-pointer transition-all"
            @click="openSession(session.id)"
          >
            <div>
              <span class="text-text-DEFAULT font-medium">{{ session.name }}</span>
              <span class="text-text-muted text-sm ml-3">{{ session.photo_count }} 张照片</span>
            </div>
            <button
              @click.stop="removeSession(session.id)"
              class="text-text-muted hover:text-red-500 transition-colors text-lg leading-none"
            >
              &times;
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Folder picker -->
    <FolderPicker
      :visible="showPicker"
      title="选择照片文件夹"
      @select="onFolderSelect"
      @close="showPicker = false"
    />
  </div>
</template>

<script setup lang="ts">
// 首页视图 - 会话列表管理、导入文件夹创建新会话
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import type { Session } from '../types/photo'
import { createSession, listSessions, deleteSession } from '../api/sessions'
import FolderPicker from '../components/common/FolderPicker.vue'

const router = useRouter()
const folderPath = ref('')
const sessions = ref<Session[]>([])
const importing = ref(false)
const error = ref('')
const importProgress = ref('')
const showPicker = ref(false)

function onFolderSelect(path: string) {
  folderPath.value = path
}

onMounted(async () => {
  try {
    sessions.value = await listSessions()
  } catch {}
})

async function importFolder() {
  if (!folderPath.value.trim()) return
  error.value = ''
  importing.value = true
  importProgress.value = '正在扫描文件夹...'

  try {
    const session = await createSession(folderPath.value.trim())
    importProgress.value = ''
    folderPath.value = ''
    router.push({ name: 'browse', params: { sessionId: session.id } })
  } catch (e: any) {
    error.value = e.response?.data?.detail || '导入失败，请检查路径是否正确'
  } finally {
    importing.value = false
  }
}

function openSession(id: string) {
  router.push({ name: 'browse', params: { sessionId: id } })
}

async function removeSession(id: string) {
  await deleteSession(id)
  sessions.value = sessions.value.filter(s => s.id !== id)
}
</script>
