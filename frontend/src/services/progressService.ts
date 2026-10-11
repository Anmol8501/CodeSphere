import type { ApiResponse } from '../types/api'
import type {
  ActivityItem,
  DifficultyProgress,
  Heatmap,
  LanguageStat,
  ProgressOverview,
  StreakInfo,
  TopicProgressItem,
} from '../types/progress'
import { api, unwrap } from './api'

/** The signed-in student's own progress (read-only; the server always uses the JWT user). */
export const progressService = {
  overview(): Promise<ProgressOverview> {
    return unwrap(api.get<ApiResponse<ProgressOverview>>('/progress/overview'))
  },

  topics(): Promise<TopicProgressItem[]> {
    return unwrap(api.get<ApiResponse<TopicProgressItem[]>>('/progress/topics'))
  },

  difficulty(): Promise<DifficultyProgress> {
    return unwrap(api.get<ApiResponse<DifficultyProgress>>('/progress/difficulty'))
  },

  languages(): Promise<LanguageStat[]> {
    return unwrap(api.get<ApiResponse<LanguageStat[]>>('/progress/languages'))
  },

  activity(limit = 20): Promise<ActivityItem[]> {
    return unwrap(api.get<ApiResponse<ActivityItem[]>>('/progress/activity', { params: { limit } }))
  },

  streak(): Promise<StreakInfo> {
    return unwrap(api.get<ApiResponse<StreakInfo>>('/progress/streak'))
  },

  heatmap(days = 365): Promise<Heatmap> {
    return unwrap(api.get<ApiResponse<Heatmap>>('/progress/heatmap', { params: { days } }))
  },
}
