import type { Tone } from '../ui/tones'
import type { SubmissionStatus, TestStatus } from '../../types/workspace'

export interface VerdictStyle {
  label: string
  tone: Tone
}

/** One place for submission-verdict wording and colors (results panel, history, badges). */
export const VERDICTS: Record<SubmissionStatus, VerdictStyle> = {
  ACCEPTED: { label: 'Accepted', tone: 'brand' },
  WRONG_ANSWER: { label: 'Wrong Answer', tone: 'danger' },
  COMPILE_ERROR: { label: 'Compilation Error', tone: 'warning' },
  RUNTIME_ERROR: { label: 'Runtime Error', tone: 'danger' },
  TIME_LIMIT_EXCEEDED: { label: 'Time Limit Exceeded', tone: 'warning' },
  MEMORY_LIMIT_EXCEEDED: { label: 'Memory Limit Exceeded', tone: 'warning' },
  OUTPUT_LIMIT_EXCEEDED: { label: 'Output Limit Exceeded', tone: 'warning' },
  SYSTEM_ERROR: { label: 'System Error', tone: 'info' },
  EXECUTION_TIMEOUT: { label: 'Execution Timeout', tone: 'info' },
  PENDING: { label: 'Pending', tone: 'neutral' },
  RUNNING: { label: 'Judging', tone: 'neutral' },
}

/** One place for per-test status wording and colors. */
export const TEST_STATUSES: Record<TestStatus, VerdictStyle> = {
  PASSED: { label: 'Passed', tone: 'brand' },
  FAILED: { label: 'Wrong Answer', tone: 'danger' },
  COMPILE_ERROR: { label: 'Compilation Error', tone: 'warning' },
  RUNTIME_ERROR: { label: 'Runtime Error', tone: 'danger' },
  TIME_LIMIT_EXCEEDED: { label: 'Time Limit Exceeded', tone: 'warning' },
  MEMORY_LIMIT_EXCEEDED: { label: 'Memory Limit Exceeded', tone: 'warning' },
  OUTPUT_LIMIT_EXCEEDED: { label: 'Output Limit Exceeded', tone: 'warning' },
  SYSTEM_ERROR: { label: 'System Error', tone: 'info' },
  EXECUTED: { label: 'Ran', tone: 'info' },
}

/** Verdicts that are about the judge, not the student's code. */
export const INFRASTRUCTURE_VERDICTS: SubmissionStatus[] = ['SYSTEM_ERROR', 'EXECUTION_TIMEOUT']

/** A test that did not fail (custom cases without an expected output just "ran"). */
export const isTestPassing = (status: TestStatus) => status === 'PASSED' || status === 'EXECUTED'

export function formatRuntime(ms: number | null | undefined): string {
  return ms === null || ms === undefined ? '-' : `${ms} ms`
}

export function formatMemory(kb: number | null | undefined): string {
  if (kb === null || kb === undefined) return '-'
  return kb >= 1024 ? `${(kb / 1024).toFixed(1)} MB` : `${kb} KB`
}

export function formatTimeLimit(ms: number): string {
  return ms % 1000 === 0 ? `${ms / 1000} s` : `${ms} ms`
}

export function formatLimits(timeLimitMs: number, memoryLimitKb: number): string {
  return `${formatTimeLimit(timeLimitMs)} · ${Math.round(memoryLimitKb / 1024)} MB`
}

/** "61.2%" or "-" when there is nothing to divide. */
export function formatPercent(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(value)) return '-'
  return `${Number.isInteger(value) ? value : value.toFixed(1)}%`
}
