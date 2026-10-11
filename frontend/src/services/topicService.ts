import type { ApiResponse } from '../types/api'
import type { Topic, TopicDetail } from '../types/problem'
import { api, unwrap } from './api'

export const topicService = {
  /** Active top-level topics in learning-path order. */
  list(): Promise<Topic[]> {
    return unwrap(api.get<ApiResponse<Topic[]>>('/topics'))
  },

  get(slug: string): Promise<TopicDetail> {
    return unwrap(api.get<ApiResponse<TopicDetail>>(`/topics/${encodeURIComponent(slug)}`))
  },
}
