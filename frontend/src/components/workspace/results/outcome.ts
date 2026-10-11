import type { Language } from '../../../types/problem'
import type { RunResult, SubmissionDetail, SubmissionStatus, TestResult } from '../../../types/workspace'
import { INFRASTRUCTURE_VERDICTS } from '../verdicts'

/** The latest RUN or SUBMIT result shown in the workspace, with the exact code that was judged. */
export type WorkspaceOutcome =
  | { mode: 'run'; language: Language; languageLabel: string; sourceCode: string; result: RunResult }
  | { mode: 'submit'; language: Language; languageLabel: string; sourceCode: string; submission: SubmissionDetail }

export const testKey = (t: TestResult) => `${t.kind}-${t.index}`

export function testLabel(t: TestResult): string {
  return t.kind === 'custom' ? `Custom ${t.index}` : `Test Case ${t.index}`
}

/** One shape for a run or a submission, so every panel reads the same fields. */
export interface OutcomeView {
  isRun: boolean
  submissionId: number | null
  verdict: SubmissionStatus
  passed: number
  total: number
  runtimeMs: number | null
  memoryKb: number | null
  timeLimitMs: number | null
  memoryLimitKb: number | null
  tests: TestResult[]
  notRun: number
  infrastructure: boolean
  /** Compiler output when the code did not compile. */
  compileText: string | null
  /** Safe error message (public stderr, hidden-test notice, or judge status). */
  message: string | null
}

export function viewOf(outcome: WorkspaceOutcome): OutcomeView {
  if (outcome.mode === 'run') {
    const r = outcome.result
    return {
      isRun: true,
      submissionId: null,
      verdict: r.verdict,
      passed: r.passed_tests,
      total: r.total_tests,
      runtimeMs: r.runtime_ms,
      memoryKb: r.memory_kb,
      timeLimitMs: r.time_limit_ms,
      memoryLimitKb: r.memory_limit_kb,
      tests: r.results,
      notRun: 0,
      infrastructure: INFRASTRUCTURE_VERDICTS.includes(r.verdict),
      compileText: r.compile_output,
      message: r.message,
    }
  }
  const s = outcome.submission
  const compile = s.status === 'COMPILE_ERROR'
  return {
    isRun: false,
    submissionId: s.id,
    verdict: s.status,
    passed: s.passed_tests,
    total: s.total_tests,
    runtimeMs: s.runtime_ms,
    memoryKb: s.memory_kb,
    timeLimitMs: s.time_limit_ms,
    memoryLimitKb: s.memory_limit_kb,
    tests: s.results,
    notRun: s.not_run_tests,
    infrastructure: INFRASTRUCTURE_VERDICTS.includes(s.status),
    compileText: compile ? s.error_message : null,
    message: compile ? null : s.error_message,
  }
}
