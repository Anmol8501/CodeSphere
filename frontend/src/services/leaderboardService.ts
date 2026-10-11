import type { ApiResponse } from '../types/api'
import type { LeaderboardPage } from '../types/progress'
import { api, unwrap } from './api'

export const leaderboardService = {
  /** Global ranking (public fields only: rank, name, solved, acceptance rate). */
  get({ page = 1, limit = 20 }: { page?: number; limit?: number } = {}): Promise<LeaderboardPage> {
    return unwrap(api.get<ApiResponse<LeaderboardPage>>('/leaderboard', { params: { scope: 'global', page, limit } }))
  },
}
