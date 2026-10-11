import { CheckCircle2, Loader2, RefreshCw, XCircle } from 'lucide-react'
import { Link } from 'react-router-dom'
import { cn } from '../../../utils/format'
import { PerformanceCards } from '../../submissions/PerformanceCards'
import { TestResultList } from '../../submissions/TestResultList'
import { VerdictBadge } from '../../submissions/VerdictBadge'
import { Button } from '../../ui/Button'
import { OutputTerminal } from './OutputTerminal'
import { viewOf, type WorkspaceOutcome } from './outcome'

interface ResultViewProps {
  outcome: WorkspaceOutcome | null
  busy: 'run' | 'submit' | null
  onRetry: () => void
}

export function BusyState({ busy }: { busy: 'run' | 'submit' }) {
  return (
    <div className="flex h-full min-h-28 flex-col items-center justify-center gap-2 text-center" role="status" aria-live="polite">
      <Loader2 className="size-5 animate-spin text-brand-500" aria-hidden />
      <p className="text-sm font-semibold text-ink-950">{busy === 'run' ? 'Running your code...' : 'Judging your submission...'}</p>
      <p className="text-xs text-ink-500">{busy === 'run' ? 'Public tests and your custom cases.' : 'All tests, including hidden ones.'}</p>
    </div>
  )
}

/** Verdict banner, runtime / memory and per-test results. Only the server decides any verdict shown here. */
export function ResultView({ outcome, busy, onRetry }: ResultViewProps) {
  if (busy) return <BusyState busy={busy} />
  if (!outcome) {
    return (
      <div className="flex h-full min-h-28 flex-col items-center justify-center gap-1.5 px-4 text-center">
        <span className="font-mono text-xs font-bold tracking-[0.2em] text-brand-500">READY TO RUN</span>
        <p className="max-w-md text-sm text-ink-500">
          <strong className="text-ink-800">Run</strong> checks the public tests and your custom cases.{' '}
          <strong className="text-ink-800">Submit</strong> judges every test, including hidden ones.
        </p>
      </div>
    )
  }

  const v = viewOf(outcome)
  const accepted = v.verdict === 'ACCEPTED'
  const compileError = v.verdict === 'COMPILE_ERROR'
  return (
    <div className="space-y-3" aria-live="polite">
      <div
        className={cn(
          'flex flex-wrap items-center justify-between gap-2 rounded-xl border px-3.5 py-3',
          accepted && 'border-brand-500/40 bg-brand-500/[0.07]',
          !accepted && v.infrastructure && 'border-info/30 bg-info/[0.06]',
          !accepted && !v.infrastructure && 'border-danger/30 bg-danger/[0.05]',
        )}
      >
        <div className="flex min-w-0 items-center gap-2.5">
          {!v.infrastructure &&
            (accepted ? (
              <CheckCircle2 className="size-6 shrink-0 text-brand-500" aria-hidden />
            ) : (
              <XCircle className="size-6 shrink-0 text-danger" aria-hidden />
            ))}
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-2">
              <VerdictBadge verdict={v.verdict} className="text-xs" />
              <span className="font-mono text-[11px] text-ink-400">
                {v.isRun ? 'Run' : `Submission #${v.submissionId}`} · {outcome.languageLabel}
              </span>
            </div>
            {!v.infrastructure && !compileError && (
              <p className="mt-1.5 text-sm font-semibold text-ink-950">
                {v.passed} / {v.total} {v.isRun ? 'public ' : ''}test case{v.total === 1 ? '' : 's'} passed
              </p>
            )}
          </div>
        </div>
      </div>

      {!v.infrastructure && !compileError && (
        <PerformanceCards
          compact
          runtimeMs={v.runtimeMs}
          memoryKb={v.memoryKb}
          timeLimitMs={v.timeLimitMs}
          memoryLimitKb={v.memoryLimitKb}
          verdict={v.verdict}
        />
      )}

      {v.infrastructure && (
        <div className="flex flex-wrap items-center justify-between gap-2 rounded-xl border border-info/30 bg-info/10 px-3.5 py-3 text-sm">
          <p className="text-ink-900">{v.message ?? 'Code execution service is temporarily unavailable.'} Your code and draft are safe.</p>
          <Button size="sm" variant="secondary" icon={<RefreshCw className="size-3.5" aria-hidden />} onClick={onRetry}>
            Try again
          </Button>
        </div>
      )}

      {v.compileText && <OutputTerminal blocks={[{ label: 'Compiler output', text: v.compileText, tone: 'error' }]} />}
      {!v.isRun && !v.infrastructure && !compileError && v.message && (
        <OutputTerminal blocks={[{ label: 'Error', text: v.message, tone: 'error' }]} />
      )}

      <TestResultList key={v.submissionId ?? `run-${v.verdict}-${v.tests.length}`} tests={v.tests} notRun={v.notRun} />

      {!v.isRun && (
        <p className="text-xs text-ink-500">
          Saved to your{' '}
          <Link to={`/student/submissions/${v.submissionId}`} className="font-semibold text-brand-400 hover:underline">
            submission history
          </Link>
          .
        </p>
      )}
    </div>
  )
}
