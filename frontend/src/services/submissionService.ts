import type { ApiResponse } from '../types/api'
import type { Paginated } from '../types/problem'
import type { SubmissionDetail, SubmissionListParams, SubmissionSummary } from '../types/workspace'
import { api, unwrap } from './api'

/** The signed-in student's own submissions (the backend scopes every call to the JWT user). */
export const submissionService = {
  list({ problem, problemId, language, status, search, period, page = 1, limit = 20 }: SubmissionListParams = {}): Promise<Paginated<SubmissionSummary>> {
    return unwrap(
      api.get<ApiResponse<Paginated<SubmissionSummary>>>('/submissions', {
        params: {
          problem,
          problem_id: problemId,
          language,
          status,
          search: search?.trim() || undefined,
          period: period === 'all' ? undefined : period,
          page,
          limit,
        },
      }),
    )
  },

  get(id: number): Promise<SubmissionDetail> {
    return unwrap(api.get<ApiResponse<SubmissionDetail>>(`/submissions/${id}`))
  },
}
