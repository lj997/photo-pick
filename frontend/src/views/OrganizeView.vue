<template>
  <div class="h-screen overflow-hidden bg-bg text-text-DEFAULT">
    <header class="h-14 flex items-center justify-between border-b border-border bg-bg-raised px-4 shadow-card">
      <div class="flex min-w-0 items-center gap-3">
        <button class="btn-icon" title="返回浏览" @click="$router.push({ name: 'browse', params: { sessionId } })">
          <ArrowLeft class="h-4 w-4" />
        </button>
        <div class="flex h-9 w-9 items-center justify-center rounded-lg bg-accent/10 text-accent">
          <FolderTree class="h-5 w-5" />
        </div>
        <div class="min-w-0">
          <div class="text-sm font-semibold">照片整理</div>
          <div class="text-xs text-text-muted">独立整理当前项目的全部原始照片，不依赖挑选结果</div>
        </div>
      </div>
      <button class="btn-primary inline-flex items-center gap-2" :disabled="running || !canRun" @click="runOrganize">
        <MoveRight class="h-4 w-4" />
        {{ running ? '整理中...' : config.mode === 'move' ? '开始移动' : '开始复制' }}
      </button>
    </header>

    <main class="grid h-[calc(100vh-56px)] grid-cols-[360px_minmax(0,1fr)] overflow-hidden">
      <aside class="overflow-y-auto border-r border-border bg-bg-raised p-4">
        <section class="space-y-3">
          <h2 class="text-xs font-semibold text-text-secondary">目标文件夹</h2>
          <div class="flex gap-2">
            <input v-model="config.destination" class="input-base" placeholder="选择整理后的照片目录" @blur="refreshPreview" />
            <button class="rounded-lg border border-border px-3 text-sm font-medium hover:border-accent hover:text-accent" @click="showPicker = true">浏览</button>
          </div>
        </section>

        <section class="mt-6 space-y-3">
          <h2 class="text-xs font-semibold text-text-secondary">整理方式</h2>
          <div class="grid grid-cols-2 gap-2">
            <button :class="modeClass('copy')" @click="config.mode = 'copy'">
              <Copy class="h-4 w-4" />
              复制
            </button>
            <button :class="modeClass('move')" @click="config.mode = 'move'">
              <Scissors class="h-4 w-4" />
              移动
            </button>
          </div>
          <p class="text-xs text-text-muted">默认来源是当前项目的全部照片。移动会更新项目中的原图路径；不确定时建议先复制。</p>
        </section>

        <section class="mt-6 space-y-3">
          <h2 class="text-xs font-semibold text-text-secondary">分组目录</h2>
          <div class="flex flex-wrap gap-2">
            <button
              v-for="option in groupOptions"
              :key="option.value"
              :class="['inline-flex items-center gap-1.5 rounded-lg border px-2.5 py-1.5 text-xs font-medium transition-all',
                config.group_by.includes(option.value) ? 'border-accent bg-accent text-white' : 'border-border bg-bg-raised text-text-secondary hover:border-accent/50 hover:text-text-DEFAULT']"
              @click="toggleGroup(option.value)"
            >
              <component :is="option.icon" class="h-3.5 w-3.5" />
              {{ option.label }}
            </button>
          </div>
          <div class="rounded-lg bg-surface/70 px-3 py-2 text-xs text-text-secondary">
            当前路径：{{ pathPattern || '不分组，直接放入目标目录' }}
          </div>
          <div class="rounded-lg border border-border bg-surface/40 p-2">
            <div class="mb-2 text-xs font-semibold text-text-secondary">内容标签生成方式</div>
            <div class="space-y-1.5">
              <button
                v-for="method in tagMethods"
                :key="method.value"
                :class="['w-full rounded-lg border px-3 py-2 text-left transition-all',
                  selectedTagMethod === method.value ? 'border-accent bg-accent/10' : 'border-border bg-bg-raised hover:border-accent/40']"
                @click="selectedTagMethod = method.value"
              >
                <div class="flex items-center justify-between gap-2">
                  <span class="text-xs font-semibold text-text-DEFAULT">{{ method.label }}</span>
                  <span :class="['rounded-full px-2 py-0.5 text-[11px] font-medium', method.badgeClass]">{{ method.cost }}</span>
                </div>
                <p class="mt-1 text-xs text-text-muted">{{ method.desc }}</p>
              </button>
            </div>
            <button
              class="mt-2 inline-flex w-full items-center justify-center gap-2 rounded-lg bg-accent px-3 py-2 text-sm font-medium text-white transition-colors hover:bg-accent-hover disabled:opacity-50"
              :disabled="taggingRunning"
              @click="runSelectedTagging"
            >
              <Sparkles class="h-4 w-4" />
              {{ taggingRunning ? '正在生成标签...' : '按所选方式生成标签' }}
            </button>
          </div>
        </section>

        <section class="mt-6 space-y-3">
          <h2 class="text-xs font-semibold text-text-secondary">范围筛选（可选）</h2>
          <p class="text-xs text-text-muted">不选择任何条件时，会整理当前项目里的全部照片。</p>
          <label class="flex items-center justify-between gap-3 text-sm">
            <span class="text-text-secondary">最低评分</span>
            <select v-model.number="starsMin" class="rounded-lg border border-border bg-bg-raised px-2 py-1 text-sm">
              <option :value="undefined">不限</option>
              <option v-for="n in [1, 2, 3, 4, 5]" :key="n" :value="n">{{ n }} 星及以上</option>
            </select>
          </label>
          <div>
            <div class="mb-2 text-xs text-text-muted">状态</div>
            <div class="grid grid-cols-3 gap-2">
              <button v-for="s in statuses" :key="s.value" :class="filterButtonClass(selectedStatuses.includes(s.value))" @click="toggleStatus(s.value)">
                {{ s.label }}
              </button>
            </div>
          </div>
          <div>
            <div class="mb-2 text-xs text-text-muted">色标</div>
            <div class="flex gap-2">
              <button
                v-for="c in colors"
                :key="c.value"
                :class="['h-7 w-7 rounded-full border-2 transition-all', selectedColors.includes(c.value) ? 'border-text-DEFAULT scale-110' : 'border-transparent opacity-70 hover:opacity-100']"
                :style="{ background: c.hex }"
                :title="c.label"
                @click="toggleColor(c.value)"
              ></button>
            </div>
          </div>
        </section>

        <section class="mt-6 space-y-3">
          <h2 class="text-xs font-semibold text-text-secondary">文件命名</h2>
          <input v-model="config.rename_template" class="input-base" placeholder="可选：{date}_{seq}_{original}" @blur="refreshPreview" />
          <p class="text-xs text-text-muted">可用：{date} {time} {seq} {original} {camera} {stars} {status}</p>
          <label class="flex items-center gap-2 text-sm text-text-secondary">
            <input v-model="config.include_note_template" type="checkbox" class="accent-accent" />
            整理后创建照片故事笔记
          </label>
        </section>
      </aside>

      <section class="flex min-w-0 flex-col overflow-hidden">
        <div class="grid grid-cols-3 gap-px border-b border-border bg-border">
          <div class="bg-bg-raised p-4">
            <div class="text-xs text-text-muted">将处理</div>
            <div class="mt-1 text-2xl font-semibold">{{ preview?.total ?? 0 }}</div>
          </div>
          <div class="bg-bg-raised p-4">
            <div class="text-xs text-text-muted">目标分组</div>
            <div class="mt-1 text-2xl font-semibold">{{ preview?.groups.length ?? 0 }}</div>
          </div>
          <div class="bg-bg-raised p-4">
            <div class="text-xs text-text-muted">上次结果</div>
            <div class="mt-1 text-sm font-medium" :class="result ? 'text-emerald-600' : 'text-text-muted'">
              {{ result ? `完成 ${result.processed}，跳过 ${result.skipped}` : '尚未执行' }}
            </div>
          </div>
        </div>

        <div class="grid flex-1 min-h-0 grid-cols-[260px_minmax(0,1fr)_420px] overflow-hidden">
          <aside class="min-h-0 overflow-y-auto border-r border-border bg-bg-raised p-3">
            <div class="mb-3 flex items-center justify-between">
              <h2 class="text-sm font-semibold">目录预览</h2>
              <button class="rounded-lg px-2 py-1 text-xs font-medium text-text-muted hover:bg-surface-hover hover:text-text-DEFAULT" :disabled="manualCount === 0" @click="clearManualAdjustments">
                清除调整
              </button>
            </div>
            <div v-if="error" class="mb-3 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">{{ error }}</div>
            <div v-if="!preview" class="flex h-64 items-center justify-center rounded-lg border border-dashed border-border text-sm text-text-muted">
              选择目标文件夹后生成整理预览
            </div>
            <div v-else class="space-y-2">
              <button
                v-for="group in preview.groups"
                :key="group.path"
                :class="['w-full rounded-lg border p-3 text-left transition-all',
                  selectedGroupPath === group.path ? 'border-accent bg-accent/5 shadow-card' : 'border-border bg-bg-raised hover:border-accent/40']"
                @click="selectGroup(group.path)"
              >
                <div class="flex items-center justify-between gap-3">
                  <div class="min-w-0">
                    <div class="truncate text-sm font-medium">{{ group.path }}</div>
                    <div class="mt-1 truncate text-xs text-text-muted">{{ group.sample_filenames.join(' · ') }}</div>
                  </div>
                  <span class="rounded-full bg-accent/10 px-2 py-1 text-xs font-semibold text-accent">{{ group.count }}</span>
                </div>
              </button>
            </div>
          </aside>

          <section class="flex min-h-0 flex-col overflow-hidden">
            <div class="border-b border-border bg-bg-raised p-3">
              <div class="mb-3 flex items-center justify-between gap-3">
                <div class="min-w-0">
                  <h2 class="truncate text-sm font-semibold">{{ selectedGroupPath || '照片明细' }}</h2>
                  <p class="text-xs text-text-muted">
                    {{ visiblePhotos.length }} 张 · 已选 {{ selectedPhotoIds.length }} 张 · 手动调整 {{ manualCount }} 张
                  </p>
                </div>
                <button class="inline-flex items-center gap-1.5 rounded-lg border border-border px-3 py-1.5 text-xs font-medium hover:border-accent hover:text-accent" :disabled="loadingPreview || !config.destination" @click="refreshPreview">
                  <RefreshCw class="h-3.5 w-3.5" />
                  {{ loadingPreview ? '生成中...' : '刷新预览' }}
                </button>
              </div>

              <div class="mb-3 flex flex-wrap gap-2">
                <button class="toolbar-btn" :disabled="visiblePhotos.length === 0" @click="selectAllVisible">
                  全选当前目录
                </button>
                <button class="toolbar-btn" :disabled="visiblePhotos.length === 0" @click="invertVisibleSelection">
                  反选
                </button>
                <button class="toolbar-btn" :disabled="selectedPhotoIds.length === 0" @click="selectedPhotoIds = []">
                  清空选择
                </button>
              </div>

              <div class="grid grid-cols-[minmax(0,1fr)_auto] gap-2">
                <input v-model="manualTarget" class="input-base py-1.5 text-xs" placeholder="输入新目录，例如 2026-旅行/上海" @keyup.enter="moveSelectedToManualTarget" />
                <button class="rounded-lg bg-accent px-3 py-1.5 text-xs font-medium text-white hover:bg-accent-hover" :disabled="selectedPhotoIds.length === 0 || !manualTarget.trim()" @click="moveSelectedToManualTarget">
                  移动所选
                </button>
              </div>
              <div class="mt-2 grid grid-cols-[minmax(0,1fr)_auto] gap-2">
                <input v-model="groupRenameTarget" class="input-base py-1.5 text-xs" placeholder="把当前目录整体改为，例如 家庭/生日" @keyup.enter="renameCurrentGroup" />
                <button class="rounded-lg border border-border px-3 py-1.5 text-xs font-medium hover:border-accent hover:text-accent" :disabled="visiblePhotos.length === 0 || !groupRenameTarget.trim()" @click="renameCurrentGroup">
                  改当前目录
                </button>
              </div>
              <div class="mt-2 flex flex-wrap gap-1.5">
                <button
                  v-for="path in allGroupPaths"
                  :key="path"
                  class="rounded-lg border border-border px-2 py-1 text-xs text-text-secondary hover:border-accent hover:text-accent"
                  :disabled="selectedPhotoIds.length === 0"
                  @click="moveSelectedTo(path)"
                >
                  放入 {{ path }}
                </button>
              </div>
              <div v-if="tagWarning" class="mt-3 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-800">
                {{ tagWarning }}
              </div>
              <div v-if="localTagMessage" class="mt-3 rounded-lg border border-emerald-200 bg-emerald-50 px-3 py-2 text-xs text-emerald-800">
                {{ localTagMessage }}
              </div>
            </div>

            <div v-if="!preview" class="flex flex-1 items-center justify-center text-sm text-text-muted">
              生成预览后可查看照片细节并手动调整目录
            </div>
            <div v-else-if="visiblePhotos.length === 0" class="flex flex-1 items-center justify-center text-sm text-text-muted">
              当前目录没有照片
            </div>
            <div v-else class="grid flex-1 auto-rows-min grid-cols-[repeat(auto-fill,minmax(150px,1fr))] gap-3 overflow-y-auto p-4">
              <div
                v-for="photo in visiblePhotos"
                :key="photo.id"
                :class="['group overflow-hidden rounded-lg border bg-bg-raised shadow-card transition-all',
                  selectedPhotoIds.includes(photo.id) ? 'border-accent ring-2 ring-accent/20' : 'border-border hover:border-accent/40']"
              >
                <div class="relative aspect-[4/3] bg-surface">
                  <img :src="getThumbnailUrl(photo.id, 'lg')" :alt="photo.filename" class="h-full w-full object-cover" loading="lazy" @click="detailPhoto = photo" />
                  <label class="absolute left-2 top-2 flex h-7 w-7 items-center justify-center rounded-lg bg-black/55 text-white">
                    <input :checked="selectedPhotoIds.includes(photo.id)" type="checkbox" class="accent-accent" @change="togglePhotoSelection(photo.id)" />
                  </label>
                  <button class="absolute right-2 top-2 rounded-lg bg-black/55 px-2 py-1 text-xs text-white opacity-0 transition-opacity group-hover:opacity-100" @click="detailPhoto = photo">
                    详情
                  </button>
                </div>
                <div class="space-y-1 p-2">
                  <div class="truncate text-xs font-medium" :title="photo.filename">{{ photo.filename }}</div>
                  <div class="truncate text-[11px] text-text-muted">{{ formatTakenAt(photo.taken_at) }} · {{ photo.camera_model || '未知相机' }}</div>
                  <div class="flex items-center justify-between gap-2">
                    <span class="truncate text-[11px] text-accent" :title="photo.target_path">{{ photo.target_path }}</span>
                    <button class="text-[11px] font-medium text-text-muted hover:text-accent" @click="resetPhotoManual(photo.id)" v-if="manualPaths[photo.id]">还原</button>
                  </div>
                </div>
              </div>
            </div>
          </section>

          <aside class="flex min-h-0 flex-col border-l border-border bg-bg-raised">
            <div v-if="detailPhoto" class="border-b border-border p-4">
              <div class="mb-3 flex items-center justify-between">
                <h2 class="text-sm font-semibold">照片详情</h2>
                <button class="text-xs text-text-muted hover:text-text-DEFAULT" @click="detailPhoto = null">收起</button>
              </div>
              <img :src="getFullPhotoUrl(detailPhoto.id)" :alt="detailPhoto.filename" class="mb-3 max-h-48 w-full rounded-lg bg-surface object-contain" />
              <div class="space-y-1 text-xs text-text-secondary">
                <div class="font-medium text-text-DEFAULT">{{ detailPhoto.filename }}</div>
                <div>目标目录：<span class="text-accent">{{ detailPhoto.target_path }}</span></div>
                <div>拍摄时间：{{ formatTakenAt(detailPhoto.taken_at) }}</div>
                <div>相机：{{ detailPhoto.camera_model || '未知' }}</div>
                <div>镜头：{{ detailPhoto.lens || '未知' }}</div>
                <div>格式：{{ detailPhoto.format || '未知' }}</div>
                <div v-if="detailPhoto.tags.length">标签：{{ detailPhoto.tags.join(' · ') }}</div>
              </div>
              <div class="mt-3 flex gap-2">
                <input v-model="detailTarget" class="input-base py-1.5 text-xs" placeholder="手动目标目录" />
                <button class="rounded-lg bg-accent px-3 text-xs font-medium text-white" :disabled="!detailTarget.trim()" @click="movePhotoTo(detailPhoto.id, detailTarget)">
                  应用
                </button>
              </div>
            </div>

            <div class="border-b border-border p-4">
              <div class="flex items-center justify-between">
                <h2 class="text-sm font-semibold">照片故事笔记</h2>
                <button class="inline-flex items-center gap-1.5 rounded-lg bg-accent px-3 py-1.5 text-xs font-medium text-white hover:bg-accent-hover" :disabled="!noteDirectory" @click="saveStoryNote">
                  <Save class="h-3.5 w-3.5" />
                  保存
                </button>
              </div>
              <p class="mt-1 text-xs text-text-muted">Markdown 保存为 PHOTO_STORY.md，位于整理后的目标目录。</p>
            </div>
            <div class="flex gap-1 border-b border-border p-2">
              <button v-for="tool in noteTools" :key="tool.label" class="rounded-lg px-2 py-1 text-xs font-medium text-text-secondary hover:bg-surface-hover hover:text-text-DEFAULT" @click="insertNote(tool.syntax)">
                {{ tool.label }}
              </button>
            </div>
            <textarea v-model="noteContent" class="min-h-0 flex-1 resize-none border-0 bg-bg-raised p-4 font-mono text-sm leading-6 outline-none" placeholder="# 照片故事&#10;&#10;写下这组照片背后的故事..." />
            <div class="max-h-56 overflow-y-auto border-t border-border p-4">
              <div class="mb-2 text-xs font-semibold text-text-secondary">预览</div>
              <div class="prose-preview" v-html="renderedNote"></div>
            </div>
          </aside>
        </div>
      </section>
    </main>

    <FolderPicker
      :visible="showPicker"
      title="选择整理目标文件夹"
      @select="onFolderSelect"
      @close="showPicker = false"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import {
  ArrowLeft,
  CalendarDays,
  Camera,
  Clock,
  Copy,
  FileType,
  FolderTree,
  MapPin,
  MoveRight,
  Palette,
  RefreshCw,
  Save,
  Scissors,
  Sparkles,
  Star,
  Tag,
} from 'lucide-vue-next'
import FolderPicker from '../components/common/FolderPicker.vue'
import {
  applyOrganize,
  previewOrganize,
  readNote,
  saveNote,
  type OrganizeConfig,
  type OrganizePhotoPreview,
  type OrganizePreview,
  type OrganizeResult,
} from '../api/organizer'
import { getFullPhotoUrl, getThumbnailUrl } from '../api/photos'
import { getSession } from '../api/sessions'
import { generateLocalTags, getSessionTagSummary } from '../api/tags'
import { getAISettings, startContentAnalysis } from '../api/aiSettings'
import type { TagSummary } from '../types/photo'

const route = useRoute()
const sessionId = computed(() => route.params.sessionId as string)

const config = ref<OrganizeConfig>({
  destination: '',
  mode: 'copy',
  group_by: ['month', 'status'],
  include_note_template: true,
})

const preview = ref<OrganizePreview | null>(null)
const result = ref<OrganizeResult | null>(null)
const loadingPreview = ref(false)
const running = ref(false)
const error = ref('')
const showPicker = ref(false)
const selectedStatuses = ref<string[]>([])
const selectedColors = ref<string[]>([])
const starsMin = ref<number | undefined>(undefined)
const noteContent = ref(defaultNote())
const selectedGroupPath = ref('')
const selectedPhotoIds = ref<string[]>([])
const manualTarget = ref('')
const groupRenameTarget = ref('')
const detailTarget = ref('')
const detailPhoto = ref<OrganizePhotoPreview | null>(null)
const manualPaths = ref<Record<string, string>>({})
const tagSummary = ref<TagSummary>({ dimensions: [] })
const taggingRunning = ref(false)
const localTagMessage = ref('')
const selectedTagMethod = ref<'rules' | 'vision' | 'remote' | 'ai'>('rules')

const statuses = [
  { value: 'accepted', label: '入选' },
  { value: 'pending', label: '待定' },
  { value: 'rejected', label: '淘汰' },
]

const colors = [
  { value: 'red', hex: '#ef4444', label: '红色' },
  { value: 'yellow', hex: '#eab308', label: '黄色' },
  { value: 'green', hex: '#22c55e', label: '绿色' },
  { value: 'blue', hex: '#3b82f6', label: '蓝色' },
  { value: 'purple', hex: '#a855f7', label: '紫色' },
]

const groupOptions = [
  { value: 'year', label: '年份', icon: CalendarDays },
  { value: 'month', label: '月份', icon: CalendarDays },
  { value: 'date', label: '日期', icon: Clock },
  { value: 'status', label: '状态', icon: Tag },
  { value: 'stars', label: '评分', icon: Star },
  { value: 'color', label: '色标', icon: Palette },
  { value: 'camera', label: '相机', icon: Camera },
  { value: 'lens', label: '镜头', icon: Camera },
  { value: 'format', label: '格式', icon: FileType },
  { value: 'tag:scene', label: '内容场景', icon: Tag },
  { value: 'tag:people', label: '人物', icon: Tag },
  { value: 'tag:setting', label: '地点/环境', icon: MapPin },
]

const noteTools = [
  { label: '标题', syntax: '## 小标题\n\n' },
  { label: '加粗', syntax: '**重点文字**' },
  { label: '清单', syntax: '- ' },
  { label: '引用', syntax: '> ' },
]

const tagMethods = [
  {
    value: 'rules' as const,
    label: '规则标签',
    cost: '免费',
    badgeClass: 'bg-emerald-100 text-emerald-700',
    desc: '只看文件名、原目录、EXIF 时间/设备/焦段，最快最稳，不识别画面内容。',
  },
  {
    value: 'vision' as const,
    label: '本地图像分析',
    cost: '免费离线',
    badgeClass: 'bg-emerald-100 text-emerald-700',
    desc: '在规则基础上分析缩略图颜色、亮度、构图，并用 OpenCV 本地人脸检测。',
  },
  {
    value: 'remote' as const,
    label: '远程兼容服务',
    cost: '低/自控',
    badgeClass: 'bg-amber-100 text-amber-700',
    desc: '走 AI 设置里的 custom/OpenAI 兼容端点，可接自建服务、局域网模型或便宜 API。',
  },
  {
    value: 'ai' as const,
    label: 'AI 大模型视觉',
    cost: '较高',
    badgeClass: 'bg-rose-100 text-rose-700',
    desc: '走已配置的 Claude/OpenAI 等视觉模型，语义最好，但会产生 API 成本。',
  },
]

const canRun = computed(() => !!config.value.destination && (preview.value?.total || 0) > 0)
const noteDirectory = computed(() => result.value?.destination || config.value.destination)
const pathPattern = computed(() => config.value.group_by.map(v => groupOptions.find(o => o.value === v)?.label || v).join(' / '))
const selectedGroup = computed(() => preview.value?.groups.find(group => group.path === selectedGroupPath.value) || preview.value?.groups[0] || null)
const visiblePhotos = computed(() => selectedGroup.value?.photos || [])
const allGroupPaths = computed(() => preview.value?.groups.map(group => group.path).filter(path => path !== selectedGroupPath.value).slice(0, 10) || [])
const manualCount = computed(() => Object.keys(manualPaths.value).length)
const selectedTagDimensions = computed(() => config.value.group_by.filter(v => v.startsWith('tag:')).map(v => v.split(':', 2)[1]))
const tagWarning = computed(() => {
  if (selectedTagDimensions.value.length === 0) return ''
  const existing = new Set(tagSummary.value.dimensions.filter(dim => dim.tags.length > 0).map(dim => dim.dimension))
  const missing = selectedTagDimensions.value.filter(dim => !existing.has(dim))
  if (missing.length === 0) return ''
  const labels: Record<string, string> = { scene: '内容场景', people: '人物', setting: '地点/环境', composition: '构图' }
  return `${missing.map(dim => labels[dim] || dim).join('、')} 当前没有标签数据。需要先做 AI 分析或手动给照片加标签，否则这些照片会归到“未标记”目录。`
})

const renderedNote = computed(() => {
  return escapeHtml(noteContent.value)
    .replace(/^### (.*)$/gm, '<h3>$1</h3>')
    .replace(/^## (.*)$/gm, '<h2>$1</h2>')
    .replace(/^# (.*)$/gm, '<h1>$1</h1>')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/^> (.*)$/gm, '<blockquote>$1</blockquote>')
    .replace(/^- (.*)$/gm, '<li>$1</li>')
    .replace(/\n/g, '<br>')
})

function modeClass(mode: 'copy' | 'move') {
  return [
    'inline-flex items-center justify-center gap-2 rounded-lg border px-3 py-2 text-sm font-medium transition-all',
    config.value.mode === mode ? 'border-accent bg-accent text-white' : 'border-border bg-bg-raised text-text-secondary hover:border-accent/50 hover:text-text-DEFAULT',
  ]
}

function filterButtonClass(active: boolean) {
  return [
    'rounded-lg border px-2.5 py-1.5 text-xs font-medium transition-all',
    active ? 'border-accent bg-accent text-white' : 'border-border bg-bg-raised text-text-secondary hover:border-accent/50',
  ]
}

function buildConfig(): OrganizeConfig {
  return {
    ...config.value,
    filters: {
      stars_min: starsMin.value,
      status: selectedStatuses.value.length ? selectedStatuses.value : undefined,
      colors: selectedColors.value.length ? selectedColors.value : undefined,
    },
    rename_template: config.value.rename_template?.trim() || undefined,
    manual_paths: manualCount.value > 0 ? manualPaths.value : undefined,
  }
}

async function refreshPreview() {
  if (!config.value.destination) return
  loadingPreview.value = true
  error.value = ''
  try {
    preview.value = await previewOrganize(sessionId.value, buildConfig())
    if (!selectedGroupPath.value || !preview.value.groups.some(group => group.path === selectedGroupPath.value)) {
      selectedGroupPath.value = preview.value.groups[0]?.path || ''
    }
    selectedPhotoIds.value = selectedPhotoIds.value.filter(id => preview.value?.groups.some(group => group.photos.some(photo => photo.id === id)))
    if (detailPhoto.value) {
      detailPhoto.value = preview.value.groups.flatMap(group => group.photos).find(photo => photo.id === detailPhoto.value?.id) || null
    }
  } catch (e: any) {
    error.value = e.response?.data?.detail || '生成预览失败'
  } finally {
    loadingPreview.value = false
  }
}

async function runOrganize() {
  if (!canRun.value) return
  running.value = true
  error.value = ''
  try {
    result.value = await applyOrganize(sessionId.value, buildConfig())
    await loadStoryNote()
    await refreshPreview()
  } catch (e: any) {
    error.value = e.response?.data?.detail || '整理失败'
  } finally {
    running.value = false
  }
}

async function loadStoryNote() {
  if (!noteDirectory.value) return
  const note = await readNote(noteDirectory.value)
  noteContent.value = note.exists ? note.content : defaultNote()
}

async function saveStoryNote() {
  if (!noteDirectory.value) return
  const saved = await saveNote(noteDirectory.value, noteContent.value)
  result.value = result.value || { total: 0, processed: 0, skipped: 0, destination: noteDirectory.value, note_path: saved.path }
}

function onFolderSelect(path: string) {
  config.value.destination = path
  showPicker.value = false
  refreshPreview()
  loadStoryNote()
}

function toggleGroup(value: string) {
  const list = config.value.group_by
  config.value.group_by = list.includes(value) ? list.filter(v => v !== value) : [...list, value]
  refreshPreview()
}

function selectGroup(path: string) {
  selectedGroupPath.value = path
  selectedPhotoIds.value = []
}

function toggleStatus(value: string) {
  selectedStatuses.value = selectedStatuses.value.includes(value) ? selectedStatuses.value.filter(v => v !== value) : [...selectedStatuses.value, value]
  refreshPreview()
}

function toggleColor(value: string) {
  selectedColors.value = selectedColors.value.includes(value) ? selectedColors.value.filter(v => v !== value) : [...selectedColors.value, value]
  refreshPreview()
}

function selectAllVisible() {
  const ids = visiblePhotos.value.map(photo => photo.id)
  selectedPhotoIds.value = Array.from(new Set([...selectedPhotoIds.value, ...ids]))
}

function invertVisibleSelection() {
  const visibleIds = new Set(visiblePhotos.value.map(photo => photo.id))
  const outside = selectedPhotoIds.value.filter(id => !visibleIds.has(id))
  const invertedInside = visiblePhotos.value.filter(photo => !selectedPhotoIds.value.includes(photo.id)).map(photo => photo.id)
  selectedPhotoIds.value = [...outside, ...invertedInside]
}

function insertNote(syntax: string) {
  noteContent.value += syntax
}

function togglePhotoSelection(photoId: string) {
  selectedPhotoIds.value = selectedPhotoIds.value.includes(photoId)
    ? selectedPhotoIds.value.filter(id => id !== photoId)
    : [...selectedPhotoIds.value, photoId]
}

async function moveSelectedTo(path: string) {
  if (selectedPhotoIds.value.length === 0) return
  for (const id of selectedPhotoIds.value) {
    manualPaths.value[id] = path
  }
  selectedPhotoIds.value = []
  await refreshPreview()
}

async function moveSelectedToManualTarget() {
  const target = manualTarget.value.trim()
  if (!target) return
  await moveSelectedTo(target)
  manualTarget.value = ''
}

async function renameCurrentGroup() {
  const target = groupRenameTarget.value.trim()
  if (!target || visiblePhotos.value.length === 0) return
  for (const photo of visiblePhotos.value) {
    manualPaths.value[photo.id] = target
  }
  groupRenameTarget.value = ''
  selectedPhotoIds.value = []
  await refreshPreview()
}

async function movePhotoTo(photoId: string, path: string) {
  const target = path.trim()
  if (!target) return
  manualPaths.value[photoId] = target
  detailTarget.value = ''
  await refreshPreview()
}

async function resetPhotoManual(photoId: string) {
  const next = { ...manualPaths.value }
  delete next[photoId]
  manualPaths.value = next
  await refreshPreview()
}

async function clearManualAdjustments() {
  manualPaths.value = {}
  selectedPhotoIds.value = []
  await refreshPreview()
}

async function runSelectedTagging() {
  taggingRunning.value = true
  localTagMessage.value = ''
  error.value = ''
  try {
    if (selectedTagMethod.value === 'rules' || selectedTagMethod.value === 'vision') {
      const result = await generateLocalTags(sessionId.value, selectedTagMethod.value)
      tagSummary.value = await getSessionTagSummary(sessionId.value)
      const modeLabel = selectedTagMethod.value === 'rules' ? '规则标签' : '本地图像分析'
      localTagMessage.value = `${modeLabel}完成：为 ${result.tagged}/${result.total} 张照片生成 ${result.tags_created} 个标签${result.failed ? `，${result.failed} 张已降级处理` : ''}。`
    } else {
      const settings = await getAISettings()
      if (!settings.ai_enabled) {
        throw new Error('AI/远程识别未启用，请先在 AI 设置中配置。')
      }
      if (selectedTagMethod.value === 'remote' && settings.ai_provider !== 'custom') {
        localTagMessage.value = '当前不是 custom 端点，将使用现有 AI 设置发起内容分析。'
      }
      await startContentAnalysis(sessionId.value)
      localTagMessage.value = selectedTagMethod.value === 'remote'
        ? '已启动远程兼容服务分析。完成后刷新预览即可看到新标签。'
        : '已启动 AI 大模型内容分析。完成后刷新预览即可看到新标签。'
    }
    await refreshPreview()
  } catch (e: any) {
    error.value = e.response?.data?.detail || e.message || '生成标签失败'
  } finally {
    taggingRunning.value = false
  }
}

function formatTakenAt(value: string | null) {
  if (!value) return '无拍摄时间'
  return value.slice(0, 16).replace('T', ' ')
}

function escapeHtml(value: string) {
  return value.replace(/[&<>"']/g, ch => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[ch] || ch))
}

function defaultNote() {
  return '# 照片故事\n\n## 这组照片记录了什么\n\n- \n\n## 值得记住的瞬间\n\n- \n\n## 人物、地点与细节\n\n- \n'
}

function defaultDestination(folderPath: string) {
  const trimmed = folderPath.replace(/[\\/]+$/, '')
  const sep = trimmed.includes('\\') ? '\\' : '/'
  return `${trimmed}${sep}照片整理`
}

onMounted(async () => {
  try {
    const [session, summary] = await Promise.all([
      getSession(sessionId.value),
      getSessionTagSummary(sessionId.value),
    ])
    tagSummary.value = summary
    if (!config.value.destination) {
      config.value.destination = defaultDestination(session.folder_path)
      await refreshPreview()
      await loadStoryNote()
    }
  } catch (e: any) {
    error.value = e.response?.data?.detail || '初始化整理页失败'
  }
})

watch(starsMin, () => refreshPreview())
</script>

<style scoped>
.prose-preview {
  color: #4b5563;
  font-size: 0.875rem;
  line-height: 1.65;
}

.prose-preview :deep(h1),
.prose-preview :deep(h2),
.prose-preview :deep(h3) {
  color: #111827;
  font-weight: 700;
  margin: 0.5rem 0;
}

.prose-preview :deep(blockquote) {
  border-left: 3px solid #2563eb;
  padding-left: 0.75rem;
  color: #4b5563;
}

.prose-preview :deep(li) {
  margin-left: 1rem;
}

.toolbar-btn {
  border: 1px solid #d8dee8;
  border-radius: 0.5rem;
  padding: 0.375rem 0.625rem;
  font-size: 0.75rem;
  font-weight: 500;
  color: #4b5563;
  background: #ffffff;
  transition: color 0.15s ease, border-color 0.15s ease, background-color 0.15s ease;
}

.toolbar-btn:hover:not(:disabled) {
  border-color: #2563eb;
  color: #2563eb;
}

.toolbar-btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}
</style>
