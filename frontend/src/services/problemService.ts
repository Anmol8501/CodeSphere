import type { ApiResponse } from '../types/api'
import type { Problem, ProblemListParams, ProblemListResponse, Tag } from '../types/problem'
import { api, unwrap } from './api'

export const problemService = {
  /** Server-side search, filters and pagination (published problems only). */
  list({ search, difficulty, topic, tags, status, page = 1, pageSize = 20 }: ProblemListParams = {}): Promise<ProblemListResponse> {
    return unwrap(
      api.get<ApiResponse<ProblemListResponse>>('/problems', {
        params: {
          search: search?.trim() || undefined,
          difficulty,
          topic,
          tags: tags?.length ? tags.join(',') : undefined,
          status,
          page,
          page_size: pageSize,
        },
      }),
    )
  },

  get(slug: string): Promise<Problem> {
    return unwrap(api.get<ApiResponse<Problem>>(`/problems/${encodeURIComponent(slug)}`))
  },

  listTags(): Promise<Tag[]> {
    return unwrap(api.get<ApiResponse<Tag[]>>('/tags'))
  },
}
