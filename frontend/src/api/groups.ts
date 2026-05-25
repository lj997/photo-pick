import api from './index'
import type { Group } from '../types/photo'

export async function listGroups(sessionId: string, groupType?: string, includeMembers = false): Promise<Group[]> {
  const params: Record<string, any> = {}
  if (groupType) params.group_type = groupType
  if (includeMembers) params.include_members = true
  const { data } = await api.get(`/sessions/${sessionId}/groups`, { params })
  return data
}

export async function getGroup(groupId: string): Promise<Group> {
  const { data } = await api.get(`/groups/${groupId}`)
  return data
}

export async function detectSimilarGroups(sessionId: string, threshold?: number): Promise<void> {
  const params: Record<string, any> = {}
  if (threshold !== undefined) params.threshold = threshold
  await api.post(`/sessions/${sessionId}/groups/detect-similar`, null, { params })
}

export async function updateGroupPick(groupId: string, pickPhotoId: string | null): Promise<void> {
  await api.patch(`/groups/${groupId}`, { pick_photo_id: pickPhotoId })
}

export async function resetGroupPK(groupId: string): Promise<void> {
  await api.post(`/groups/${groupId}/reset`)
}
