<template>
  <div v-if="visible" class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm" @click.self="close">
    <div class="bg-white rounded-2xl shadow-elevated w-[540px] max-h-[80vh] flex flex-col">
      <!-- Header -->
      <div class="px-6 py-5 border-b border-border flex items-center justify-between">
        <h2 class="text-lg font-semibold text-text-DEFAULT">导出照片</h2>
        <button @click="close" class="text-text-muted hover:text-text-DEFAULT text-xl leading-none">&times;</button>
      </div>

      <!-- Body -->
      <div class="flex-1 overflow-y-auto px-6 py-5 space-y-5">
        <!-- Destination folder -->
        <div>
          <label class="block text-sm font-medium text-text-DEFAULT mb-1.5">目标文件夹</label>
          <div class="flex gap-2">
            <input
              v-model="destination"
              type="text"
              placeholder="例如 E:\output\selected"
              class="input-base flex-1"
            />
            <button
              @click="showFolderPicker = true"
              class="px-3 py-2 rounded-lg text-sm font-medium border border-border text-text-DEFAULT hover:border-text-muted transition-all whitespace-nowrap"
            >浏览</button>
          </div>
        </div>

        <!-- Export mode -->
        <div>
          <label class="block text-sm font-medium text-text-DEFAULT mb-2">导出方式</label>
          <div class="flex gap-2">
            <button
              @click="mode = 'copy'"
              :class="['flex-1 px-3 py-2.5 rounded-lg text-sm font-medium transition-all border', mode === 'copy' ? 'bg-accent-muted border-accent text-accent' : 'bg-white border-border text-text-DEFAULT hover:border-text-muted']"
            >复制（保留原件）</button>
            <button
              @click="mode = 'move'"
              :class="['flex-1 px-3 py-2.5 rounded-lg text-sm font-medium transition-all border', mode === 'move' ? 'bg-accent-muted border-accent text-accent' : 'bg-white border-border text-text-DEFAULT hover:border-text-muted']"
            >移动</button>
          </div>
        </div>

        <!-- Filter -->
        <div>
          <label class="block text-sm font-medium text-text-DEFAULT mb-2">筛选 - 选择要导出的照片</label>
          <div class="space-y-2.5">
            <!-- Status filter -->
            <div class="flex items-center gap-2">
              <span class="text-xs text-text-muted w-14">状态:</span>
              <button
                v-for="s in statusOptions"
                :key="s.value"
                @click="toggleFilterStatus(s.value)"
                :class="['px-2.5 py-1 rounded-lg text-xs font-medium transition-all border', filterStatus.includes(s.value) ? 'bg-accent text-white shadow-sm border-accent' : 'bg-bg-raised text-text-secondary border-border hover:text-text-DEFAULT hover:border-text-muted']"
              >{{ s.label }}</button>
            </div>
            <!-- Stars filter -->
            <div class="flex items-center gap-2">
              <span class="text-xs text-text-muted w-14">评分:</span>
              <button
                v-for="n in 6"
                :key="n - 1"
                @click="filterStarsMin = (filterStarsMin === n - 1 ? null : n - 1)"
                :class="['px-2.5 py-1 rounded-lg text-xs font-medium transition-all border', filterStarsMin === (n - 1) ? 'bg-accent text-white shadow-sm border-accent' : 'bg-bg-raised text-text-secondary border-border hover:text-text-DEFAULT hover:border-text-muted']"
              >{{ n - 1 === 0 ? '全部' : '>=' + (n - 1) + '★' }}</button>
            </div>
            <!-- Color filter -->
            <div class="flex items-center gap-2">
              <span class="text-xs text-text-muted w-14">色标:</span>
              <button
                v-for="c in colorOptions"
                :key="c.value"
                @click="toggleFilterColor(c.value)"
                :class="['w-5 h-5 rounded-full border-2 transition-transform hover:scale-110', filterColors.includes(c.value) ? 'border-text-DEFAULT scale-110' : 'border-transparent opacity-60']"
                :style="{ background: c.hex }"
              ></button>
              <button
                v-if="filterColors.length > 0"
                @click="filterColors = []"
                class="text-xs text-text-muted hover:text-text-DEFAULT ml-1"
              >清除</button>
            </div>
          </div>
        </div>

        <!-- Group by (subfolder organization) -->
        <div>
          <label class="block text-sm font-medium text-text-DEFAULT mb-2">按分类创建子文件夹</label>
          <div class="flex gap-2">
            <button
              v-for="(opt, idx) in groupByOptions"
              :key="idx"
              @click="groupBy = (groupBy === opt.value ? null : opt.value)"
              :class="['px-3 py-1.5 rounded-lg text-xs font-medium transition-all border', groupBy === opt.value ? 'bg-accent text-white shadow-sm border-accent' : 'bg-bg-raised text-text-secondary border-border hover:text-text-DEFAULT hover:border-text-muted']"
            >{{ opt.label }}</button>
          </div>
          <p v-if="groupBy" class="text-xs text-text-muted mt-2">
            {{ groupByHint }}
          </p>
        </div>

        <!-- Rename template -->
        <div>
          <label class="block text-sm font-medium text-text-DEFAULT mb-1.5">重命名（可选）</label>
          <input
            v-model="renameTemplate"
            type="text"
            placeholder="{date}_{seq}_{original}"
            class="input-base"
          />
          <p class="text-xs text-text-muted mt-1.5">可用变量: {date}, {time}, {seq}, {original}, {camera}</p>
        </div>
      </div>

      <!-- Footer -->
      <div class="px-6 py-4 border-t border-border flex items-center justify-between">
        <div class="text-sm text-text-secondary">
          <span v-if="!exporting">{{ matchInfo }}</span>
          <span v-else>{{ exportProgress }}</span>
        </div>
        <div class="flex gap-2">
          <button
            @click="close"
            class="px-4 py-2 rounded-lg text-sm font-medium text-text-secondary hover:text-text-DEFAULT bg-bg-raised border border-border hover:border-text-muted transition-all"
          >取消</button>
          <button
            @click="doExport"
            :disabled="!canExport || exporting"
            class="btn-primary disabled:opacity-40"
          >{{ exporting ? '导出中...' : '开始导出' }}</button>
        </div>
      </div>
    </div>

    <!-- Folder picker for export destination -->
    <FolderPicker
      :visible="showFolderPicker"
      title="选择导出目标文件夹"
      :initial-path="destination"
      @select="onDestinationSelect"
      @close="showFolderPicker = false"
    />
  </div>
</template>

<script setup lang="ts">
// 导出弹窗 - 配置导出目标、模式（复制/移动）、筛选条件、分组和重命名规则
import { ref, computed, watch } from 'vue'
import { usePhotosStore } from '../../stores/photos'
import { startExport, getExportStatus } from '../../api/export'
import type { ExportConfig } from '../../types/photo'
import FolderPicker from '../common/FolderPicker.vue'

const props = defineProps<{ visible: boolean }>()
const emit = defineEmits<{ close: [] }>()

const photos = usePhotosStore()

const destination = ref('')
const showFolderPicker = ref(false)
const mode = ref<'copy' | 'move'>('copy')
const groupBy = ref<'status' | 'color' | 'stars' | null>(null)
const filterStatus = ref<string[]>(['accepted'])
const filterStarsMin = ref<number | null>(null)
const filterColors = ref<string[]>([])
const renameTemplate = ref('')
const exporting = ref(false)
const exportedCount = ref(0)
const exportTotal = ref(0)

const statusOptions = [
  { value: 'accepted', label: '入选' },
  { value: 'pending', label: '待定' },
  { value: 'rejected', label: '淘汰' },
]

const colorOptions = [
  { value: 'red', hex: '#ef4444' },
  { value: 'yellow', hex: '#eab308' },
  { value: 'green', hex: '#22c55e' },
  { value: 'blue', hex: '#3b82f6' },
  { value: 'purple', hex: '#a855f7' },
]

const groupByOptions = [
  { value: null, label: '不分组' },
  { value: 'status', label: '按状态' },
  { value: 'color', label: '按色标' },
  { value: 'stars', label: '按评分' },
] as const

const groupByHint = computed(() => {
  if (groupBy.value === 'status') return '将创建: accepted/, pending/, rejected/'
  if (groupBy.value === 'color') return '将创建: red/, yellow/, green/, blue/, purple/, no_label/'
  if (groupBy.value === 'stars') return '将创建: 0_stars/, 1_stars/, ... 5_stars/'
  return ''
})

const canExport = computed(() => {
  return destination.value.trim().length > 0
})

const matchInfo = computed(() => {
  if (filterStatus.value.length === 0 && filterStarsMin.value === null && filterColors.value.length === 0) {
    return `将导出全部 ${photos.total} 张照片`
  }
  return '将按筛选条件导出'
})

const exportProgress = computed(() => {
  return `已导出 ${exportedCount.value} / ${exportTotal.value}`
})

function toggleFilterStatus(value: string) {
  const idx = filterStatus.value.indexOf(value)
  if (idx >= 0) {
    filterStatus.value.splice(idx, 1)
  } else {
    filterStatus.value.push(value)
  }
}

function toggleFilterColor(value: string) {
  const idx = filterColors.value.indexOf(value)
  if (idx >= 0) {
    filterColors.value.splice(idx, 1)
  } else {
    filterColors.value.push(value)
  }
}

async function doExport() {
  if (!canExport.value || exporting.value) return

  const config: ExportConfig = {
    destination: destination.value.trim(),
    mode: mode.value,
    group_by: groupBy.value,
    filter_status: filterStatus.value.length > 0 ? filterStatus.value : undefined,
    filter_stars_min: filterStarsMin.value ?? undefined,
    filter_colors: filterColors.value.length > 0 ? filterColors.value : undefined,
    rename_template: renameTemplate.value.trim() || undefined,
  }

  exporting.value = true
  exportedCount.value = 0

  try {
    const sessionId = photos.photos[0]?.session_id
    if (!sessionId) return

    const job = await startExport(sessionId, config)
    exportTotal.value = job.total_count

    const pollInterval = setInterval(async () => {
      try {
        const status = await getExportStatus(job.id)
        exportedCount.value = status.processed_count
        if (status.status === 'completed' || status.status === 'failed') {
          clearInterval(pollInterval)
          exporting.value = false
          if (status.status === 'completed') {
            setTimeout(() => close(), 1500)
          }
        }
      } catch {
        clearInterval(pollInterval)
        exporting.value = false
      }
    }, 1000)
  } catch (e: any) {
    exporting.value = false
    alert(e.response?.data?.detail || '导出失败')
  }
}

function close() {
  if (!exporting.value) {
    emit('close')
  }
}

function onDestinationSelect(path: string) {
  destination.value = path
}

watch(() => props.visible, (v) => {
  if (v) {
    exporting.value = false
    exportedCount.value = 0
  }
})
</script>
