import api from './index'

export interface OrganizeFilter {
  stars_min?: number
  status?: string[]
  colors?: string[]
  tag?: string
}

export interface OrganizeConfig {
  destination: string
  mode: 'copy' | 'move'
  group_by: string[]
  filters?: OrganizeFilter
  rename_template?: string
  include_note_template: boolean
  manual_paths?: Record<string, string>
}

export interface OrganizePhotoPreview {
  id: string
  filename: string
  target_path: string
  taken_at: string | null
  camera_model: string | null
  lens: string | null
  format: string | null
  file_size: number | null
  stars: number
  color_label: string | null
  status: string
  tags: string[]
}

export interface OrganizeGroupPreview {
  path: string
  count: number
  sample_filenames: string[]
  photos: OrganizePhotoPreview[]
}

export interface OrganizePreview {
  total: number
  destination: string
  groups: OrganizeGroupPreview[]
}

export interface OrganizeResult {
  total: number
  processed: number
  skipped: number
  destination: string
  note_path: string | null
}

export interface NoteRead {
  path: string
  exists: boolean
  content: string
}

export async function previewOrganize(sessionId: string, config: OrganizeConfig): Promise<OrganizePreview> {
  const { data } = await api.post(`/sessions/${sessionId}/organizer/preview`, config)
  return data
}

export async function applyOrganize(sessionId: string, config: OrganizeConfig): Promise<OrganizeResult> {
  const { data } = await api.post(`/sessions/${sessionId}/organizer/apply`, config)
  return data
}

export async function readNote(directory: string, filename = 'PHOTO_STORY.md'): Promise<NoteRead> {
  const { data } = await api.get('/organizer/note', { params: { directory, filename } })
  return data
}

export async function saveNote(directory: string, content: string, filename = 'PHOTO_STORY.md'): Promise<{ path: string; saved: boolean }> {
  const { data } = await api.post('/organizer/note', { directory, filename, content })
  return data
}
