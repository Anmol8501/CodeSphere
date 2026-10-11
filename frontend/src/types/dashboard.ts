import type { Role } from './auth'
import type { DifficultyProgress, Recommendation } from './progress'

// Shapes returned by the dashboard endpoints. Values for features that don't
// exist yet (contests, classrooms) are zero/empty, never sample data.

export interface DashboardUser {
  id: number
  full_name: string
  email: string
  role: Role
}

export interface StudentStatistics {
  /** Distinct published problems with an ACCEPTED submission. */
  problems_solved: number
  total_problems: number
  attempted_problems: number
  /** Judged submissions. */
  total_attempts: number
  accepted_submissions: number
  /** accepted / judged submissions, 0–100. */
  acceptance_rate: number
  current_streak: number
  longest_streak: number
  active_today: boolean
  contest_rating: number | null
}

export interface TopicProgress {
  slug: string
  topic: string
  solved: number
  total: number
  percent: number
}

export interface StudentDashboardData {
  user: DashboardUser
  statistics: StudentStatistics
  difficulty: DifficultyProgress
  learning_progress: TopicProgress[]
  /** Rule-based suggestions from the student's real progress. */
  continue_learning: Recommendation[]
  /** Calendar days (streaks) are counted in this timezone. */
  timezone: string
}

export interface StaffDashboardData {
  user: DashboardUser
  statistics: {
    students: number
    classrooms: number
    assignments: number
    contests: number
  }
}

export type ServiceState = 'online' | 'offline' | 'not_connected'

export interface ServiceStatus {
  key: string
  name: string
  status: ServiceState
  detail: string
}

export interface AdminDashboardData {
  total_users: number
  total_students: number
  total_staff: number
  total_admins: number
  active_users: number
  inactive_users: number
  system_status: ServiceStatus[]
}
