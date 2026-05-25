/**
 * 标签 API - 照片标签 CRUD、会话标签统计
 */
import api from './index'
import type { PhotoTag, TagSummary } from '../types/photo'

export async function getPhotoTags(photoId: string): Promise<PhotoTag[]> {
  const { data } = await api.get(`/photos/${photoId}/tags`)
  return data
}

export async function addPhotoTag(photoId: string, dimension: string, tagValue: string): Promise<PhotoTag> {
  const { data } = await api.post(`/photos/${photoId}/tags`, { dimension, tag_value: tagValue })
  return data
}

export async function updatePhotoTag(photoId: string, tagId: string, dimension: string, tagValue: string): Promise<PhotoTag> {
  const { data } = await api.put(`/photos/${photoId}/tags/${tagId}`, { dimension, tag_value: tagValue })
  return data
}

export async function deletePhotoTag(photoId: string, tagId: string): Promise<void> {
  await api.delete(`/photos/${photoId}/tags/${tagId}`)
}

export async function getSessionTagSummary(sessionId: string): Promise<TagSummary> {
  const { data } = await api.get(`/sessions/${sessionId}/tags/summary`)
  return data
}
