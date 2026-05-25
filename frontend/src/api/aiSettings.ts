/**
 * AI 设置 API - 获取/更新 AI 模型配置、测试连接
 */
import api from './index'
import type { AISettings } from '../types/photo'

export async function getAISettings(): Promise<AISettings> {
  const { data } = await api.get('/ai-settings')
  return data
}

export async function updateAISettings(settings: Partial<AISettings>): Promise<AISettings> {
  const { data } = await api.put('/ai-settings', settings)
  return data
}

export async function testAIConnection(): Promise<{ ok: boolean; message: string }> {
  const { data } = await api.post('/ai-settings/test')
  return data
}

export async function startContentAnalysis(sessionId: string): Promise<void> {
  await api.post(`/sessions/${sessionId}/analyze`, { types: ['content_tags'] })
}

export async function detectContentGroups(sessionId: string): Promise<{ groups_created: number }> {
  const { data } = await api.post(`/sessions/${sessionId}/groups/detect-content`)
  return data
}
