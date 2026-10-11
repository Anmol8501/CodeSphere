import type {
  AdminProblem,
  AdminProblemListItem,
  AdminProblemListParams,
  ProblemCreatePayload,
  ProblemPayload,
  TestCase,
  TestCasePayload,
} from '../types/adminProblem'
import type { ApiResponse } from '../types/api'
import type { Paginated, Tag } from '../types/problem'
import { api, unwrap } from './api'

export const adminProblemService = {
  list({ search, difficulty, topic, status, page = 1, pageSize = 10 }: AdminProblemListParams = {}): Promise<
    Paginated<AdminProblemListItem>
  > {
    return unwrap(
      api.get<ApiResponse<Paginated<AdminProblemListItem>>>('/admin/problems', {
        params: { search: search?.trim() || undefined, difficulty, topic, status, page, page_size: pageSize },
      }),
    )
  },

  get(id: number): Promise<AdminProblem> {
    return unwrap(api.get<ApiResponse<AdminProblem>>(`/admin/problems/${id}`))
  },

  create(payload: ProblemCreatePayload): Promise<AdminProblem> {
    return unwrap(api.post<ApiResponse<AdminProblem>>('/admin/problems', payload))
  },

  update(id: number, payload: ProblemPayload): Promise<AdminProblem> {
    return unwrap(api.put<ApiResponse<AdminProblem>>(`/admin/problems/${id}`, payload))
  },

  setPublished(id: number, isPublished: boolean): Promise<AdminProblem> {
    return unwrap(api.patch<ApiResponse<AdminProblem>>(`/admin/problems/${id}/publish`, { is_published: isPublished }))
  },

  /** Soft delete: the problem moves to ARCHIVED and disappears for students. */
  archive(id: number): Promise<AdminProblem> {
    return unwrap(api.delete<ApiResponse<AdminProblem>>(`/admin/problems/${id}`))
  },

  listTestCases(problemId: number): Promise<TestCase[]> {
    return unwrap(api.get<ApiResponse<TestCase[]>>(`/admin/problems/${problemId}/test-cases`))
  },

  addTestCase(problemId: number, payload: TestCasePayload): Promise<TestCase> {
    return unwrap(api.post<ApiResponse<TestCase>>(`/admin/problems/${problemId}/test-cases`, payload))
  },

  updateTestCase(id: number, payload: TestCasePayload): Promise<TestCase> {
    return unwrap(api.put<ApiResponse<TestCase>>(`/admin/test-cases/${id}`, payload))
  },

  async deleteTestCase(id: number): Promise<void> {
    await api.delete(`/admin/test-cases/${id}`)
  },

  createTag(name: string): Promise<Tag> {
    return unwrap(api.post<ApiResponse<Tag>>('/admin/tags', { name }))
  },
}
