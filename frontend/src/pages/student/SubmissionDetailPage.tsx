import { ArrowLeft, Award, CheckCircle2, Code2, ListChecks, XCircle } from 'lucide-react'
import { useCallback } from 'react'
import { Link, useParams } from 'react-router-dom'
import { LazyCodeViewer } from '../../components/submissions/LazyCodeViewer'
import { PerformanceCards } from '../../components/submissions/PerformanceCards'
import { TestResultList } from '../../components/submissions/TestResultList'
import { VerdictBadge } from '../../components/submissions/VerdictBadge'
import { DifficultyBadge } from '../../components/problems/DifficultyBadge'
import { Badge } from '../../components/ui/Badge'
import { ButtonLink } from '../../components/ui/Button'
import { SectionCard } from '../../components/ui/Card'
import { ErrorState } from '../../components/ui/ErrorState'
import { PageSkeleton } from '../../components/ui/LoadingState'
import { OutputTerminal } from '../../components/workspace/results/OutputTerminal'
import { formatMemory, formatTimeLimit, INFRASTRUCTURE_VERDICTS } from '../../components/workspace/verdicts'
import { LANGUAGE_CONFIG } from '../../config/languages'
import { useApiQuery } from '../../hooks/useApiQuery'
import { useAppTimezone } from '../../hooks/useAppTimezone'
import { submissionService } from '../../services/submissionService'
import type { SubmissionDetail } from '../../types/workspace'
import { formatDateTime, timeAgo } from '../../utils/dates'
import { cn } from '../../utils/format'

function backLinks(problemSlug?: string) {
  return (
    <div className="mb-4 flex flex-wrap gap-x-5 gap-y-2">
      {problemSlug && (
        <Link to={`/student/problems/${problemSlug}`} className="inline-flex items-center gap-1.5 text-sm font-semibold text-ink-500 transition hover:text-brand-400">
          <ArrowLeft className="size-4" aria-hidden /> Back to Problem
        </Link>
      )}
      <Link to="/student/submissions" className="inline-flex items-center gap-1.5 text-sm font-semibold text-ink-500 transition hover:text-brand-400">
        <ArrowLeft className="size-4" aria-hidden /> Back to Submissions
      </Link>
    </div>
  )
}

function LimitExplanation({ s }: { s: SubmissionDetail }) {
  if (s.status === 'TIME_LIMIT_EXCEEDED' && s.time_limit_ms) {
    return (
      <p className="text-sm text-ink-700">
        Time limit for {LANGUAGE_CONFIG[s.language].label}: <strong className="font-mono">{formatTimeLimit(s.time_limit_ms)}</strong>
        {s.runtime_ms !== null && (
          <>
            {' '}· your program was stopped after <strong className="font-mono">{s.runtime_ms} ms</strong>
          </>
        )}
        .
      </p>
    )
  }
  if (s.status === 'MEMORY_LIMIT_EXCEEDED' && s.memory_limit_kb) {
    return (
      <p className="text-sm text-ink-700">
        Memory limit: <strong className="font-mono">{formatMemory(s.memory_limit_kb)}</strong>
        {s.memory_kb !== null && (
          <>
            {' '}· peak memory <strong className="font-mono">{formatMemory(s.memory_kb)}</strong>
          </>
        )}
        .
      </p>
    )
  }
  return null
}

/** One of the student's own submissions. Someone else's id is "not found". */
export default function SubmissionDetailPage() {
  const { id } = useParams()
  const submissionId = Number(id)
  const valid = Number.isInteger(submissionId) && submissionId > 0
  const fetchSubmission = useCallback(
    () => (valid ? submissionService.get(submissionId) : Promise.reject(new Error('Submission not found.'))),
    [submissionId, valid],
  )
  const { data: s, loading, error, reload } = useApiQuery(fetchSubmission)
  const timezone = useAppTimezone()

  if (!valid) {
    return (
      <div>
        {backLinks()}
        <ErrorState title="Unable to load submission." message="Submission not found." />
      </div>
    )
  }
  if (loading && !s) return <PageSkeleton />
  if (error || !s) {
    return (
      <div>
        {backLinks()}
        <ErrorState title="Unable to load submission." message={error ?? 'No data received.'} onRetry={reload} />
      </div>
    )
  }

  const infrastructure = INFRASTRUCTURE_VERDICTS.includes(s.status)
  const accepted = s.status === 'ACCEPTED'
  const compileError = s.status === 'COMPILE_ERROR'
  const language = LANGUAGE_CONFIG[s.language].label
  const submitted = timezone ? formatDateTime(s.submitted_at, timezone) : ''

  return (
    <div className="animate-fade-in space-y-6">
      <div>
        {backLinks(s.problem.slug)}
        <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
          <div className="min-w-0">
            <p className="mb-2 font-mono text-[11px] tracking-[0.18em] text-brand-500 uppercase">Submission #{s.id}</p>
            <h1 className="text-2xl font-extrabold tracking-tight break-words text-ink-950">
              <Link to={`/student/problems/${s.problem.slug}`} className="hover:text-brand-400">
                {s.problem.title}
              </Link>
            </h1>
            <div className="mt-2 flex flex-wrap items-center gap-2.5">
              <DifficultyBadge difficulty={s.problem.difficulty} />
              <span className="font-mono text-xs text-ink-500">{language}</span>
              {s.is_first_accepted && (
                <Badge tone="brand" mono>
                  <Award className="mr-1 size-3" aria-hidden /> First solve
                </Badge>
              )}
            </div>
          </div>
          <ButtonLink to={`/student/problems/${s.problem.slug}/solve`} variant="secondary" icon={<Code2 className="size-4" aria-hidden />}>
            Open in editor
          </ButtonLink>
        </div>
      </div>

      <div
        className={cn(
          'flex flex-wrap items-center gap-3 rounded-xl border px-4 py-4',
          accepted ? 'border-brand-500/40 bg-brand-500/[0.07]' : infrastructure ? 'border-info/30 bg-info/[0.06]' : 'border-danger/30 bg-danger/[0.05]',
        )}
      >
        {!infrastructure &&
          (accepted ? <CheckCircle2 className="size-7 text-brand-500" aria-hidden /> : <XCircle className="size-7 text-danger" aria-hidden />)}
        <div className="min-w-0 flex-1">
          <VerdictBadge verdict={s.status} className="text-sm" />
          <p className="mt-1 text-sm text-ink-700">
            {infrastructure
              ? 'The judge could not finish this submission. It does not count as an attempt.'
              : compileError
                ? 'Your code did not compile, so no test was run.'
                : `${s.passed_tests} / ${s.total_tests} tests passed`}
          </p>
        </div>
        <p className="font-mono text-xs text-ink-400">
          Submitted {submitted} · <time dateTime={s.submitted_at}>{timeAgo(s.submitted_at)}</time>
        </p>
      </div>

      <PerformanceCards
        runtimeMs={s.runtime_ms}
        memoryKb={s.memory_kb}
        timeLimitMs={s.time_limit_ms}
        memoryLimitKb={s.memory_limit_kb}
        verdict={s.status}
        performance={s.performance}
        extra={[
          { label: 'Tests', value: infrastructure ? '-' : `${s.passed_tests} / ${s.total_tests}` },
          { label: 'Language', value: language },
        ]}
      />
      {accepted && s.performance && s.performance.runtime_percentile === null && (
        <p className="text-xs text-ink-400">
          Runtime and memory percentiles appear once at least {s.performance.min_sample} other students have an accepted {language} solution
          for this problem ({s.performance.compared_with} so far).
        </p>
      )}
      <LimitExplanation s={s} />

      {s.error_message && (
        <OutputTerminal
          blocks={[
            {
              label: compileError ? 'Compiler message' : infrastructure ? 'Message' : 'Error',
              text: s.error_message,
              tone: infrastructure ? 'default' : 'error',
            },
          ]}
        />
      )}

      {(s.results.length > 0 || s.not_run_tests > 0) && (
        <SectionCard title="Test Results" description="Executed in order; judging stops at the first failure" icon={<ListChecks />}>
          <TestResultList tests={s.results} notRun={s.not_run_tests} />
        </SectionCard>
      )}

      <SectionCard title="Submitted Code" description={`${language} · read-only`} icon={<Code2 />}>
        <LazyCodeViewer code={s.source_code} language={s.language} modelId={`submission-${s.id}`} ariaLabel={`Submitted ${language} code (read-only)`} />
      </SectionCard>
    </div>
  )
}
