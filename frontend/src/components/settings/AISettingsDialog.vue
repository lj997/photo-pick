<template>
  <div v-if="visible" class="fixed inset-0 z-50 flex items-center justify-center bg-black/40" @click.self="$emit('close')">
    <div class="bg-white rounded-2xl shadow-elevated w-full max-w-md mx-4 overflow-hidden">
      <!-- 标题 -->
      <div class="px-6 py-4 border-b border-border flex items-center justify-between">
        <h3 class="text-base font-semibold text-text-DEFAULT">AI 模型配置</h3>
        <button @click="$emit('close')" class="text-text-muted hover:text-text-DEFAULT text-lg">&times;</button>
      </div>

      <div class="px-6 py-5 space-y-5">
        <!-- 启用开关 -->
        <div class="flex items-center justify-between">
          <span class="text-sm text-text-DEFAULT">启用 AI 识别</span>
          <button
            @click="form.ai_enabled = !form.ai_enabled"
            :class="['w-11 h-6 rounded-full transition-colors relative', form.ai_enabled ? 'bg-accent' : 'bg-border']"
          >
            <span :class="['block w-5 h-5 rounded-full bg-white shadow absolute top-0.5 transition-transform', form.ai_enabled ? 'translate-x-[22px]' : 'translate-x-0.5']"></span>
          </button>
        </div>

        <!-- 供应商选择 -->
        <div class="space-y-1.5">
          <label class="text-xs font-medium text-text-secondary">AI 供应商</label>
          <select v-model="form.ai_provider" class="w-full border border-border rounded-lg px-3 py-2 text-sm bg-white text-text-DEFAULT">
            <option value="claude">Claude Vision (Anthropic)</option>
            <option value="openai">OpenAI GPT-4V</option>
            <option value="deepseek">DeepSeek</option>
            <option value="custom">自定义接口</option>
          </select>
        </div>

        <!-- 模型名称 -->
        <div class="space-y-1.5">
          <label class="text-xs font-medium text-text-secondary">模型名称</label>
          <input v-model="form.ai_model_name" type="text" placeholder="如 claude-sonnet-4-20250514"
            class="w-full border border-border rounded-lg px-3 py-2 text-sm bg-white text-text-DEFAULT" />
        </div>

        <!-- API Key -->
        <div class="space-y-1.5">
          <label class="text-xs font-medium text-text-secondary">API Key</label>
          <input v-model="form.ai_api_key" type="password" placeholder="输入 API 密钥"
            class="w-full border border-border rounded-lg px-3 py-2 text-sm bg-white text-text-DEFAULT" />
        </div>

        <!-- 自定义接口地址 -->
        <div v-if="form.ai_provider === 'custom'" class="space-y-1.5">
          <label class="text-xs font-medium text-text-secondary">接口地址</label>
          <input v-model="form.ai_base_url" type="text" placeholder="https://your-api.com/v1"
            class="w-full border border-border rounded-lg px-3 py-2 text-sm bg-white text-text-DEFAULT" />
        </div>

        <!-- 测试结果 -->
        <div v-if="testResult" :class="['text-xs px-3 py-2 rounded-lg', testResult.ok ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700']">
          {{ testResult.message }}
        </div>
      </div>

      <!-- 底部按钮 -->
      <div class="px-6 py-4 border-t border-border flex items-center justify-between">
        <button @click="testConnection" :disabled="testing" class="text-sm text-accent hover:text-accent-hover font-medium">
          {{ testing ? '测试中...' : '测试连接' }}
        </button>
        <div class="flex gap-2">
          <button @click="$emit('close')" class="px-4 py-2 text-sm text-text-secondary hover:text-text-DEFAULT rounded-lg hover:bg-surface-hover">取消</button>
          <button @click="save" :disabled="saving" class="btn-primary px-4 py-2 text-sm">
            {{ saving ? '保存中...' : '保存' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
// AI 配置弹窗 - 设置 AI 视觉模型供应商、密钥、开关
import { ref, watch } from 'vue'
import { getAISettings, updateAISettings, testAIConnection } from '../../api/aiSettings'
import type { AISettings } from '../../types/photo'

const props = defineProps<{ visible: boolean }>()
const emit = defineEmits<{ close: [] }>()

const form = ref<AISettings>({
  ai_enabled: false,
  ai_provider: 'claude',
  ai_model_name: 'claude-sonnet-4-20250514',
  ai_api_key: '',
  ai_base_url: '',
})

const testing = ref(false)
const saving = ref(false)
const testResult = ref<{ ok: boolean; message: string } | null>(null)

// 供应商切换时自动填充默认模型名
watch(() => form.value.ai_provider, (provider) => {
  if (provider === 'claude' && !form.value.ai_model_name) {
    form.value.ai_model_name = 'claude-sonnet-4-20250514'
  } else if (provider === 'openai' && !form.value.ai_model_name) {
    form.value.ai_model_name = 'gpt-4o'
  } else if (provider === 'deepseek' && !form.value.ai_model_name) {
    form.value.ai_model_name = 'deepseek-chat'
  }
})

watch(() => props.visible, async (v) => {
  if (v) {
    testResult.value = null
    try {
      const settings = await getAISettings()
      form.value = settings
    } catch {}
  }
})

async function testConnection() {
  testing.value = true
  testResult.value = null
  try {
    await updateAISettings(form.value)
    testResult.value = await testAIConnection()
  } catch (e: any) {
    testResult.value = { ok: false, message: e.response?.data?.detail || '连接失败' }
  } finally {
    testing.value = false
  }
}

async function save() {
  saving.value = true
  try {
    await updateAISettings(form.value)
    emit('close')
  } catch (e: any) {
    testResult.value = { ok: false, message: e.response?.data?.detail || '保存失败' }
  } finally {
    saving.value = false
  }
}
</script>
