import type { ApiResponse } from '../types/api'
import type { Paginated } from '../types/problem'
import type { AnalyticsOverview, StudentAnalyticsDetail, StudentAnalyticsRow, StudentListParams } from '../types/progress'
import { api, unwrap } from './api'

/** Staff / admin analytics. The backend enforces the role on every call. */
export const analyticsService = {
  overview(): Promise<AnalyticsOverview> {
    return unwrap(api.get<ApiResponse<AnalyticsOverview>>('/analytics/overview'))
  },

  students({ search, sort = 'solved', order = 'desc', page = 1, limit = 20 }: StudentListParams = {}): Promise<Paginated<StudentAnalyticsRow>> {
    return unwrap(
      api.get<ApiResponse<Paginated<StudentAnalyticsRow>>>('/analytics/students', {
        params: { search: search?.trim() || undefined, sort, order, page, limit },
      }),
    )
  },

  student(id: number): Promise<StudentAnalyticsDetail> {
    return unwrap(api.get<ApiResponse<StudentAnalyticsDetail>>(`/analytics/students/${id}`))
  },
}
