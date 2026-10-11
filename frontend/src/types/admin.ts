import type { Role, User } from './auth'

export interface AdminStats {
  total_students: number
  total_staff: number
  total_admins: number
  total_problems: number
  active_users: number
}

export interface UserListResponse {
  items: User[]
  total: number
  page: number
  page_size: number
}

export interface UserListParams {
  role?: Role
  /** true = active only, false = inactive only, undefined = all */
  isActive?: boolean
  search?: string
  page?: number
  pageSize?: number
}

export interface CreateStaffPayload {
  full_name: string
  email: string
  password: string
}
