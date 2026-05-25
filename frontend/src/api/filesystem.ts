/**
 * 文件系统浏览 API - 为文件夹选择器提供目录列表
 */
import api from './index'

export interface BrowseResult {
  current: string
  parent: string | null
  folders: string[]
}

export async function browseFolders(path?: string): Promise<BrowseResult> {
  const res = await api.get('/filesystem/browse', { params: { path: path || '' } })
  return res.data
}
