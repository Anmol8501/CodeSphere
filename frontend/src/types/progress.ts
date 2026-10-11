// Shapes returned by the Phase 6 progress, leaderboard and analytics endpoints.
// Every value is computed by the server from judged submissions; the client
// never sends or calculates any of them.

import type { Difficulty, Language, Paginated, TopicRef } from './problem'
import type { SubmissionStatus } from './workspace'

export interface ProgressOverview {
  total_problems: number
  solved_problems: number
  /** Tried but not solved yet. */
  attempted_problems: number
  /** Judged submissions (judge failures excluded). */
  total_submissions: number
  accepted_submissions: number
  /** accepted / judged submissions, 0–100. */
  acceptance_rate: number
}

export interface DifficultyCount {
  total: number
  solved: number
  percentage: number
}

export interface DifficultyProgress {
  easy: DifficultyCount
  medium: DifficultyCount
  hard: DifficultyCount
}

export interface TopicProgressItem {
  topic: TopicRef
  total_problems: number
  solved_problems: number
  attempted_problems: number
  percentage: number
}

export interface LanguageStat {
  language: Language
  submissions: number
  accepted: number
  acceptance_rate: number | null
  solved_problems: number
}

export interface StreakInfo {
  current_streak: number
  longest_streak: number
  active_today: boolean
  last_active_date: string | null
  activity_dates: string[]
  timezone: string
}

export interface HeatmapDay {
  /** "YYYY-MM-DD", a calendar day in the server's app timezone. */
  date: string
  submission_count: number
}

export interface Heatmap {
  start_date: string
  end_date: string
  timezone: string
  total_submissions: number
  active_days: number
  days: HeatmapDay[]
}

export interface ProblemRef {
  id: number
  slug: string
  title: string
  difficulty: Difficulty
}

/** SOLVED = first accepted, ACCEPTED = accepted again, ATTEMPTED = any other verdict. */
export type ActivityType = 'SOLVED' | 'ACCEPTED' | 'ATTEMPTED'

export interface ActivityItem {
  submission_id: number
  type: ActivityType
  verdict: SubmissionStatus
  language: Language
  problem: ProblemRef
  occurred_at: string
}

export type RecommendationReason = 'RESUME' | 'CONTINUE_TOPIC' | 'START_TOPIC'

export interface Recommendation {
  problem: ProblemRef & { topic: TopicRef }
  reason: RecommendationReason
  message: string
}

// ------------------------------------------------------------------ leaderboard
export interface LeaderboardEntry {
  rank: number
  name: string
  solved: number
  acceptance_rate: number
  is_current_user: boolean
}

export interface LeaderboardPage extends Paginated<LeaderboardEntry> {
  scope: 'global'
  current_user: LeaderboardEntry | null
  ranking_rule: string
}

// ------------------------------------------------------------------ staff / admin analytics
export interface DailyCount {
  date: string
  submissions: number
  accepted: number
}

export interface TopStudent {
  id: number
  full_name: string
  rank: number
  solved: number
  acceptance_rate: number
}

export interface AttentionItem {
  id: number
  full_name: string
  reason: 'STUCK' | 'INACTIVE'
  message: string
  solved: number
  attempts: number
  last_active_at: string | null
}

export interface ProblemInsight {
  problem: ProblemRef
  attempts: number
  solved_by: number
  acceptance_rate: number | null
}

export interface AnalyticsOverview {
  total_students: number
  active_students: number
  students_with_submissions: number
  problems_solved: number
  total_submissions: number
  submissions_today: number
  accepted_submissions: number
  accepted_today: number
  average_acceptance_rate: number
  active_window_days: number
  timezone: string
  daily: DailyCount[]
  top_students: TopStudent[]
  needs_attention: AttentionItem[]
  problems: ProblemInsight[]
}

export interface StudentAnalyticsRow {
  id: number
  full_name: string
  email: string
  is_active: boolean
  solved: number
  attempts: number
  accepted: number
  acceptance_rate: number | null
  last_active_at: string | null
  current_streak: number
}

export type StudentSort = 'solved' | 'attempts' | 'acceptance' | 'last_active' | 'name'

export interface StudentListParams {
  search?: string
  sort?: StudentSort
  order?: 'asc' | 'desc'
  page?: number
  limit?: number
}

export interface SolvedProblem {
  problem: ProblemRef
  solved_at: string
  attempts: number
  best_runtime_ms: number | null
  best_memory_kb: number | null
}

export interface StudentAnalyticsDetail {
  student: { id: number; full_name: string; email: string; is_active: boolean; joined_at: string }
  overview: ProgressOverview
  difficulty: DifficultyProgress
  topics: TopicProgressItem[]
  languages: LanguageStat[]
  streak: StreakInfo
  heatmap: Heatmap
  recent_activity: ActivityItem[]
  solved_problems: SolvedProblem[]
}
