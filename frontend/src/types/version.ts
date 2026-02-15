// 版本管理类型定义

export type VersionStatus = 'active' | 'archived' | 'rollback'

export interface VersionAuthor {
  id: number
  username: string
  avatar_url?: string
}

export interface VersionInfo {
  id: number
  skill_id: number
  version_number: string
  commit_hash: string
  commit_message: string
  author: VersionAuthor
  status: VersionStatus
  file_changes: FileChange[]
  created_at: string
  parent_version_id?: number
  tags?: string[]
}

export interface FileChange {
  file_id: number
  filename: string
  file_path: string
  change_type: 'added' | 'modified' | 'deleted' | 'renamed'
  old_path?: string
  additions: number
  deletions: number
}

export interface VersionDiff {
  version_id: number
  file_id: number
  filename: string
  old_content: string
  new_content: string
  hunks: DiffHunk[]
}

export interface DiffHunk {
  old_start: number
  old_lines: number
  new_start: number
  new_lines: number
  header?: string
  lines: DiffLine[]
}

export interface DiffLine {
  type: 'context' | 'add' | 'delete'
  old_number?: number
  new_number?: number
  content: string
}

export interface VersionListResponse {
  items: VersionInfo[]
  total: number
  page: number
  page_size: number
  has_more: boolean
}

export interface VersionSearchParams {
  search?: string
  author_id?: number
  status?: VersionStatus
  start_date?: string
  end_date?: string
  page?: number
  page_size?: number
}

export interface RevertResult {
  success: boolean
  message: string
  new_version_id?: number
  reverted_files: string[]
}

export type DiffViewMode = 'side-by-side' | 'inline'
