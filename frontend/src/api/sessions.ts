/**
 * 会话 API - 创建（导入文件夹）、列表、删除
 */
import api from './index'
import type { Session } from '../types/photo'

export async function createSession(path: string): Promise<Session> {
  const { data } = await api.post('/sessions', { path })
  return data
}

export async function listSessions(): Promise<Session[]> {
  const { data } = await api.get('/sessions')
  return data
}

export async function deleteSession(id: string): Promise<void> {
  await api.delete(`/sessions/${id}`)
}
