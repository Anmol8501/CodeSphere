// Shapes returned by the Phase 3 problem / topic / learning-path endpoints.

export type Difficulty = 'EASY' | 'MEDIUM' | 'HARD'
export type ProblemStatus = 'DRAFT' | 'PUBLISHED' | 'ARCHIVED'
export type Language = 'CPP' | 'JAVA' | 'PYTHON'
/** SOLVED needs an ACCEPTED submission; nothing is solved by just opening a problem. */
export type UserProblemStatus = 'SOLVED' | 'ATTEMPTED' | 'UNSOLVED'
export type ProgressFilter = 'solved' | 'attempted' | 'unsolved'
export type TopicProgressStatus = 'NOT_STARTED' | 'IN_PROGRESS' | 'COMPLETED'

export interface Paginated<T> {
  items: T[]
  page: number
  page_size: number
  total: number
  total_pages: number
}

export interface Tag {
  id: number
  name: string
  slug: string
}

export interface TopicRef {
  id: number
  name: string
  slug: string
}

export interface Topic extends TopicRef {
  description: string
  order_index: number
  /** Lucide icon name, e.g. "brackets". */
  icon: string | null
  parent_topic_id: number | null
  learning_outcomes: string[]
  /** Published problems only. */
  problem_count: number
}

export interface ProblemExample {
  input: string
  output: string
  explanation: string | null
  order_index: number
}

export interface StarterCode {
  language: Language
  starter_code: string
}

/** A test case the author made visible. Hidden cases are never sent to students. */
export interface SampleTestCase {
  input_data: string
  expected_output: string
  order_index: number
}

/** Aggregate statistics across all students (no personal data). */
export interface ProblemStats {
  /** Distinct students with an ACCEPTED submission. */
  solved_by: number
  /** Judged submissions (judge failures excluded). */
  attempts: number
  accepted: number
  /** accepted / attempts, 0–100; null without attempts. */
  acceptance_rate: number | null
}

/** The signed-in student's own progress on a problem. */
export interface UserProblemProgress {
  status: UserProblemStatus
  attempts: number
  accepted_submissions: number
  first_attempt_at: string | null
  last_attempt_at: string | null
  solved_at: string | null
  best_runtime_ms: number | null
  best_memory_kb: number | null
}

export interface ProblemListItem {
  id: number
  title: string
  slug: string
  difficulty: Difficulty
  topic: TopicRef
  tags: Tag[]
  user_status: UserProblemStatus
  stats: ProblemStats
}

export interface Problem extends ProblemListItem {
  description: string
  constraints: string
  input_format: string
  output_format: string
  examples: ProblemExample[]
  starter_codes: StarterCode[]
  sample_test_cases: SampleTestCase[]
  /** Languages the coding workspace offers for this problem. */
  languages: Language[]
  /** Judge limits (the time limit is scaled per language on the server). */
  time_limit_ms: number
  memory_limit_kb: number
  /** Students only (null for staff/admin). */
  progress: UserProblemProgress | null
}

export type ProblemListResponse = Paginated<ProblemListItem>

export interface ProblemListParams {
  search?: string
  difficulty?: Difficulty
  /** Topic slug. */
  topic?: string
  /** Tag slugs (a problem must have all of them). */
  tags?: string[]
  status?: ProgressFilter
  page?: number
  pageSize?: number
}

export interface LearningTopic extends Topic {
  solved_count: number
  /** Percent 0–100. */
  progress: number
  status: TopicProgressStatus
}

export interface TopicDetail extends LearningTopic {
  difficulty_counts: Record<Difficulty, number>
}

export interface LearningPath {
  topics: LearningTopic[]
  total_problems: number
  total_solved: number
  progress: number
}
