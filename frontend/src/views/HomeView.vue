<template>
  <div class="h-screen overflow-y-auto bg-bg">
    <div class="mx-auto flex min-h-full w-full max-w-6xl flex-col px-6 py-8">
      <!-- Header -->
      <div class="mb-8 flex items-center justify-between">
        <div>
          <h1 class="text-2xl font-bold text-text-DEFAULT tracking-tight">光影甄选</h1>
          <p class="mt-1 text-sm text-text-secondary">照片挑选与照片整理，两个工作流各自独立。</p>
        </div>
        <div class="hidden items-center gap-2 rounded-lg border border-border bg-bg-raised px-3 py-2 text-xs text-text-muted shadow-card sm:flex">
          <Clock3 class="h-4 w-4" />
          <span>{{ sessions.length }} 个最近项目</span>
        </div>
      </div>

      <div class="grid flex-1 gap-6 lg:grid-cols-[minmax(0,1fr)_360px]">
        <!-- Import panel -->
        <section class="flex flex-col justify-center rounded-lg border border-border bg-bg-raised p-6 shadow-card">
          <div class="mb-5 flex h-12 w-12 items-center justify-center rounded-lg bg-accent/10 text-accent">
            <FolderOpen class="h-6 w-6" />
          </div>
          <h2 class="text-xl font-semibold text-text-DEFAULT">导入照片项目</h2>
          <p class="mt-2 max-w-xl text-sm text-text-secondary">选择包含照片的文件夹，导入后可进入“照片挑选”或“照片整理”两个独立板块。</p>

          <div class="mt-7 flex flex-col gap-3 sm:flex-row">
            <input
              v-model="folderPath"
              type="text"
              placeholder="输入文件夹路径，例如 E:\Photos\2024"
              class="input-base min-h-11 flex-1"
              @keyup.enter="importFolder"
            />
            <button
              @click="showPicker = true"
              class="inline-flex min-h-11 items-center justify-center gap-2 rounded-lg border border-border px-4 text-sm font-medium text-text-DEFAULT transition-all hover:border-accent hover:text-accent"
            >
              <Search class="h-4 w-4" />
              浏览
            </button>
            <button
              @click="importFolder"
              :disabled="importing"
              class="btn-primary inline-flex min-h-11 items-center justify-center gap-2 whitespace-nowrap disabled:opacity-60"
            >
              <Upload class="h-4 w-4" />
              {{ importing ? '导入中...' : '开始导入' }}
            </button>
          </div>
          <p v-if="error" class="mt-3 text-sm text-red-600">{{ error }}</p>
          <p v-if="importProgress" class="mt-3 text-sm text-text-secondary">{{ importProgress }}</p>
        </section>

        <!-- Recent sessions -->
        <section class="rounded-lg border border-border bg-bg-raised p-4 shadow-card">
          <div class="mb-3 flex items-center justify-between">
            <h2 class="text-sm font-semibold text-text-DEFAULT">最近项目</h2>
            <span class="text-xs text-text-muted">{{ sessions.length }} 个</span>
          </div>
          <div v-if="sessions.length" class="space-y-2">
            <div
              v-for="session in sessions"
              :key="session.id"
              class="group rounded-lg border border-transparent bg-surface/60 px-3 py-3 transition-all hover:border-accent/30 hover:bg-accent/5"
            >
              <div class="mb-3 flex items-center justify-between gap-3">
                <div class="min-w-0">
                  <div class="truncate text-sm font-medium text-text-DEFAULT">{{ session.name }}</div>
                  <div class="mt-0.5 text-xs text-text-muted">{{ session.photo_count }} 张照片</div>
                </div>
                <button
                  @click.stop="removeSession(session.id)"
                  class="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg text-text-muted transition-colors hover:bg-red-50 hover:text-red-600"
                  title="删除项目"
                >
                  <Trash2 class="h-4 w-4" />
                </button>
              </div>
              <div class="grid grid-cols-2 gap-2">
                <button
                  class="inline-flex items-center justify-center gap-1.5 rounded-lg bg-accent px-3 py-2 text-xs font-medium text-white transition-colors hover:bg-accent-hover"
                  @click="openSession(session.id)"
                >
                  <Images class="h-3.5 w-3.5" />
                  照片挑选
                </button>
                <button
                  class="inline-flex items-center justify-center gap-1.5 rounded-lg border border-border bg-bg-raised px-3 py-2 text-xs font-medium text-text-DEFAULT transition-colors hover:border-accent hover:text-accent"
                  @click="openOrganizer(session.id)"
                >
                  <FolderTree class="h-3.5 w-3.5" />
                  照片整理
                </button>
              </div>
            </div>
          </div>
          <div v-else class="flex h-44 flex-col items-center justify-center rounded-lg border border-dashed border-border text-center">
            <FolderOpen class="mb-2 h-6 w-6 text-text-muted" />
            <p class="text-sm text-text-secondary">还没有最近项目</p>
          </div>
        </section>
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
import { Clock3, FolderOpen, FolderTree, Images, Search, Trash2, Upload } from 'lucide-vue-next'
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

function openOrganizer(id: string) {
  router.push({ name: 'organize', params: { sessionId: id } })
}

async function removeSession(id: string) {
  await deleteSession(id)
  sessions.value = sessions.value.filter(s => s.id !== id)
}
</script>
