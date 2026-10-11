import type {
  AdminStats,
  CreateStaffPayload,
  UserListParams,
  UserListResponse,
} from '../types/admin'
import type { ApiResponse } from '../types/api'
import type { User } from '../types/auth'
import { api, unwrap } from './api'

export const adminService = {
  getStats(): Promise<AdminStats> {
    return unwrap(api.get<ApiResponse<AdminStats>>('/admin/stats'))
  },

  listUsers({ role, isActive, search, page = 1, pageSize = 10 }: UserListParams = {}): Promise<UserListResponse> {
    return unwrap(
      api.get<ApiResponse<UserListResponse>>('/admin/users', {
        params: { role, is_active: isActive, search: search?.trim() || undefined, page, page_size: pageSize },
      }),
    )
  },

  setUserStatus(userId: number, isActive: boolean): Promise<User> {
    return unwrap(
      api.patch<ApiResponse<User>>(`/admin/users/${userId}/status`, { is_active: isActive }),
    )
  },

  createStaff(payload: CreateStaffPayload): Promise<User> {
    return unwrap(api.post<ApiResponse<User>>('/admin/staff', payload))
  },
}
