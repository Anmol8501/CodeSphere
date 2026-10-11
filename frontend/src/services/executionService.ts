import type { ApiResponse } from '../types/api'
import type { ExecutionJob, RunResult, SubmissionDetail } from '../types/workspace'
import { api, unwrap } from './api'

// Judging can take a while (queue + compile + several tests); the backend
// itself stops waiting on the judge after JUDGE0_TIMEOUT.
const EXECUTION_TIMEOUT_MS = 90_000

/**
 * The editor's only dependency for running code. It talks to the CodeArena
 * backend, which validates the request and runs the code in the Judge0
 * sandbox. The browser never talks to Judge0, and verdicts always come from
 * the server.
 */
export const executionService = {
  /** RUN: public tests + local custom cases. Nothing is stored. */
  runCode(job: ExecutionJob): Promise<RunResult> {
    return unwrap(
      api.post<ApiResponse<RunResult>>(
        '/executions/run',
        {
          problem_id: job.problemId,
          language: job.language,
          source_code: job.sourceCode,
          custom_cases: job.customCases ?? [],
        },
        { timeout: EXECUTION_TIMEOUT_MS },
      ),
    )
  },

  /** SUBMIT: public + hidden tests. Stored as an official submission. */
  submitCode(job: ExecutionJob): Promise<SubmissionDetail> {
    return unwrap(
      api.post<ApiResponse<SubmissionDetail>>(
        '/submissions',
        { problem_id: job.problemId, language: job.language, source_code: job.sourceCode },
        { timeout: EXECUTION_TIMEOUT_MS },
      ),
    )
  },
}
