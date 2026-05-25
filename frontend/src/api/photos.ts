/**
 * 照片 API - 列表查询、评分更新、缩略图/原图 URL 生成
 */
import api from './index'
import type { Photo, PhotoListResponse, MarkUpdate } from '../types/photo'

export interface PhotoListParams {
  offset?: number
  limit?: number
  sort?: string
  stars_min?: number
  stars_max?: number
  status?: string
  color_label?: string
  tag?: string
}

export async function listPhotos(sessionId: string, params: PhotoListParams = {}): Promise<PhotoListResponse> {
  const { data } = await api.get(`/sessions/${sessionId}/photos`, { params })
  return data
}

export async function getPhoto(photoId: string): Promise<Photo> {
  const { data } = await api.get(`/photos/${photoId}`)
  return data
}

export async function updateMarks(photoId: string, marks: MarkUpdate): Promise<Photo> {
  const { data } = await api.patch(`/photos/${photoId}/marks`, marks)
  return data
}

export async function batchUpdateMarks(photoIds: string[], marks: MarkUpdate): Promise<void> {
  await api.patch('/photos/batch/marks', { photo_ids: photoIds, marks })
}

export function getThumbnailUrl(photoId: string, size: 'sm' | 'lg' = 'sm'): string {
  return `/api/photos/${photoId}/thumbnail/${size}`
}

export function getFullPhotoUrl(photoId: string): string {
  return `/api/photos/${photoId}/full`
}
