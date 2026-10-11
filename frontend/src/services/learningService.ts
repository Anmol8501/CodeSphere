import type { ApiResponse } from '../types/api'
import type { LearningPath } from '../types/problem'
import { api, unwrap } from './api'

export const learningService = {
  getPath(): Promise<LearningPath> {
    return unwrap(api.get<ApiResponse<LearningPath>>('/learning-path'))
  },
}
