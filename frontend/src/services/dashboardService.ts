import type { ApiResponse } from '../types/api'
import type { AdminDashboardData, StaffDashboardData, StudentDashboardData } from '../types/dashboard'
import { api, unwrap } from './api'

export const dashboardService = {
  getStudentDashboard(): Promise<StudentDashboardData> {
    return unwrap(api.get<ApiResponse<StudentDashboardData>>('/student/dashboard'))
  },

  getStaffDashboard(): Promise<StaffDashboardData> {
    return unwrap(api.get<ApiResponse<StaffDashboardData>>('/staff/dashboard'))
  },

  getAdminDashboard(): Promise<AdminDashboardData> {
    return unwrap(api.get<ApiResponse<AdminDashboardData>>('/admin/dashboard'))
  },
}
