/**
 * 类型定义 - Photo、Session、Group、ExportConfig 等核心数据结构
 */
export interface Photo {
  id: string
  session_id: string
  filename: string
  filepath: string
  file_size: number | null
  width: number | null
  height: number | null
  format: string | null
  taken_at: string | null
  camera_make: string | null
  camera_model: string | null
  lens: string | null
  focal_length: number | null
  aperture: number | null
  shutter_speed: string | null
  iso: number | null
  stars: number
  color_label: string | null
  status: 'pending' | 'accepted' | 'rejected'
  thumb_sm_ready: boolean
  thumb_lg_ready: boolean
  sort_order: number
}

export interface Session {
  id: string
  name: string
  folder_path: string
  photo_count: number
  created_at: string
}

export interface PhotoListResponse {
  total: number
  photos: Photo[]
}

export interface MarkUpdate {
  stars?: number
  color_label?: string
  status?: string
}

export interface Group {
  id: string
  session_id: string
  name: string | null
  group_type: string
  pick_photo_id: string | null
  member_count: number
  members?: Photo[]
}

export interface AnalysisResult {
  id: string
  photo_id: string
  analysis_type: string
  score: number | null
  result_data: string | null
  is_issue: boolean
}

export interface ExportConfig {
  destination: string
  mode: 'copy' | 'move'
  group_by?: 'status' | 'color' | 'stars' | null
  filter_stars_min?: number
  filter_status?: string[]
  filter_colors?: string[]
  rename_template?: string
}

export type ColorLabel = 'red' | 'yellow' | 'green' | 'blue' | 'purple'
