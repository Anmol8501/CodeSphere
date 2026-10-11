import type {
  Difficulty,
  Language,
  ProblemExample,
  ProblemStatus,
  StarterCode,
  Tag,
  TopicRef,
} from './problem'

export interface TestCase {
  id: number
  problem_id: number
  input_data: string
  expected_output: string
  is_hidden: boolean
  order_index: number
  created_at: string
  updated_at: string
}

export interface AdminProblemListItem {
  id: number
  title: string
  slug: string
  difficulty: Difficulty
  status: ProblemStatus
  is_published: boolean
  topic: TopicRef
  tags: Tag[]
  test_case_count: number
  hidden_test_case_count: number
  created_by_name: string | null
  created_at: string
  updated_at: string
}

export interface AdminProblem extends AdminProblemListItem {
  description: string
  constraints: string
  input_format: string
  output_format: string
  time_limit_ms: number
  memory_limit_kb: number
  examples: ProblemExample[]
  /** Includes the hidden execution harness (admin only). */
  starter_codes: (StarterCode & { driver_code: string | null })[]
  test_cases: TestCase[]
}

export interface AdminProblemListParams {
  search?: string
  difficulty?: Difficulty
  topic?: string
  status?: ProblemStatus
  page?: number
  pageSize?: number
}

export interface ExamplePayload {
  input: string
  output: string
  explanation?: string | null
}

export interface StarterCodePayload {
  language: Language
  starter_code: string
  /** Hidden harness containing {{USER_CODE}} exactly once (null = full program). */
  driver_code?: string | null
}

export interface TestCasePayload {
  input_data: string
  expected_output: string
  is_hidden: boolean
  order_index?: number
}

export interface ProblemPayload {
  title: string
  slug?: string | null
  description: string
  difficulty: Difficulty
  topic_id: number
  tag_ids: number[]
  constraints: string
  input_format: string
  output_format: string
  time_limit_ms: number
  memory_limit_kb: number
  examples: ExamplePayload[]
  starter_codes: StarterCodePayload[]
  is_published?: boolean | null
}

export interface ProblemCreatePayload extends ProblemPayload {
  test_cases: TestCasePayload[]
  is_published: boolean
}
