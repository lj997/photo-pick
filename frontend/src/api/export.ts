/**
 * 导出 API - 启动导出任务、查询导出进度
 */
import api from './index'
import type { ExportConfig } from '../types/photo'

export interface ExportJob {
  id: string
  status: string
  total_count: number
  processed_count: number
}

export async function startExport(sessionId: string, config: ExportConfig): Promise<ExportJob> {
  const { data } = await api.post(`/sessions/${sessionId}/export`, config)
  return data
}

export async function getExportStatus(jobId: string): Promise<ExportJob> {
  const { data } = await api.get(`/export/${jobId}/status`)
  return data
}
