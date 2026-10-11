import type { Difficulty, Language } from './problem'

export type SupportedLanguage = Language

/** A student's saved code for one problem + language (only ever their own). */
export interface Draft {
  problem_id: number
  language: SupportedLanguage
  source_code: string
  /** Increases on every save; used to detect saves from a stale tab. */
  version: number
  updated_at: string
}

export interface DraftSavePayload {
  language: SupportedLanguage
  source_code: string
  /** Version the editor last loaded (0 = no saved draft). */
  base_version: number
  /** Overwrite a newer version saved in another tab (explicit user choice). */
  force?: boolean
}

export interface DraftSaveResult {
  saved: true
  version: number
  updated_at: string
}

/** Server-decided verdicts (the client never sends or computes one). */
export type SubmissionStatus =
  | 'PENDING'
  | 'RUNNING'
  | 'ACCEPTED'
  | 'WRONG_ANSWER'
  | 'COMPILE_ERROR'
  | 'RUNTIME_ERROR'
  | 'TIME_LIMIT_EXCEEDED'
  | 'MEMORY_LIMIT_EXCEEDED'
  | 'OUTPUT_LIMIT_EXCEEDED'
  | 'SYSTEM_ERROR'
  | 'EXECUTION_TIMEOUT'

/**
 * Outcome of ONE test case (the single per-test vocabulary used everywhere).
 * EXECUTED = a custom RUN case without an expected output (nothing to compare).
 */
export type TestStatus =
  | 'PASSED'
  | 'FAILED'
  | 'COMPILE_ERROR'
  | 'RUNTIME_ERROR'
  | 'TIME_LIMIT_EXCEEDED'
  | 'MEMORY_LIMIT_EXCEEDED'
  | 'OUTPUT_LIMIT_EXCEEDED'
  | 'SYSTEM_ERROR'
  | 'EXECUTED'

export type TestKind = 'public' | 'hidden' | 'custom'

export interface TestResult {
  /** Official tests: position ("Test Case 3"). Custom cases: position among custom cases. */
  index: number
  kind: TestKind
  status: TestStatus
  runtime_ms: number | null
  memory_kb: number | null
  /** Public / custom tests only. Always null for hidden tests. */
  input: string | null
  expected_output: string | null
  actual_output: string | null
  stderr: string | null
}

/** RUN: public tests + the student's custom cases. Not stored. */
export interface RunResult {
  verdict: SubmissionStatus
  passed_tests: number
  total_tests: number
  runtime_ms: number | null
  memory_kb: number | null
  compile_output: string | null
  message: string | null
  /** Effective limits the judge applied (time scaled for the language). */
  time_limit_ms: number | null
  memory_limit_kb: number | null
  results: TestResult[]
}

export interface SubmissionSummary {
  id: number
  problem: { id: number; slug: string; title: string; difficulty: Difficulty }
  language: SupportedLanguage
  status: SubmissionStatus
  passed_tests: number
  total_tests: number
  runtime_ms: number | null
  memory_kb: number | null
  /** The submission that first solved the problem. */
  is_first_accepted: boolean
  submitted_at: string
}

/** Percentiles vs other students' best accepted solutions; null without enough data. */
export interface SubmissionPerformance {
  runtime_percentile: number | null
  memory_percentile: number | null
  compared_with: number
  min_sample: number
}

export interface SubmissionDetail extends SubmissionSummary {
  error_message: string | null
  results: TestResult[]
  /** Tests not executed because judging stops at the first failure. */
  not_run_tests: number
  /** Effective limits the judge applied (time scaled for the language). */
  time_limit_ms: number | null
  memory_limit_kb: number | null
  performance: SubmissionPerformance | null
  finished_at: string | null
  source_code: string
}

export interface ExecutionJob {
  problemId: number
  language: SupportedLanguage
  sourceCode: string
  /** RUN only: the student's local cases (never official tests). */
  customCases?: { input: string; expected_output: string | null }[]
}

/** Calendar-day ranges, counted in the server's app timezone. */
export type SubmissionPeriod = 'today' | '7d' | '30d' | 'all'

export interface SubmissionListParams {
  /** Problem slug. */
  problem?: string
  problemId?: number
  language?: SupportedLanguage
  status?: SubmissionStatus
  /** Problem title or slug. */
  search?: string
  period?: SubmissionPeriod
  page?: number
  /** Page size (server maximum 100). */
  limit?: number
}

export type SaveState = 'initializing' | 'idle' | 'saved' | 'unsaved' | 'saving' | 'error' | 'offline' | 'conflict'

export type EditorThemeName = 'codearena-dark' | 'vs-dark' | 'hc-black'

export interface EditorSettings {
  fontSize: number
  theme: EditorThemeName
  wordWrap: boolean
  minimap: boolean
  tabSize: 2 | 4 | 8
}

/** Student-written test case. Lives only in this browser; never sent as an official test. */
export interface CustomTestCase {
  id: string
  input: string
  expected: string
}
