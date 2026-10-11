import { CheckCircle2, EyeOff } from 'lucide-react'
import { formatMemory, formatTimeLimit, isTestPassing } from '../verdicts'
import { OutputTerminal } from './OutputTerminal'
import { BusyState } from './ResultView'
import { testLabel, viewOf, type WorkspaceOutcome } from './outcome'

/**
 * Errors from the last run or submission: compiler output, runtime errors
 * (stderr of public tests only), limit failures, or the judge's own status.
 * Never shows anything about hidden test data.
 */
export function ErrorView({ outcome, busy }: { outcome: WorkspaceOutcome | null; busy: 'run' | 'submit' | null }) {
  if (busy) return <BusyState busy={busy} />
  if (!outcome) return <p className="font-mono text-xs text-ink-400">Run or submit your code to see compiler and runtime errors here.</p>

  const v = viewOf(outcome)
  if (v.compileText) {
    return (
      <div className="space-y-2">
        <p className="text-sm font-semibold text-warning">Compilation Error</p>
        <OutputTerminal blocks={[{ label: 'Compiler output', text: v.compileText, tone: 'error' }]} />
      </div>
    )
  }
  if (v.infrastructure) {
    return <p className="text-sm text-ink-700">{v.message ?? 'Code execution service is temporarily unavailable.'} Your code and draft are safe.</p>
  }

  const failing = v.tests.find((t) => t.kind !== 'custom' && !isTestPassing(t.status)) ?? v.tests.find((t) => !isTestPassing(t.status))
  if (!failing) {
    return (
      <p className="flex items-center gap-2 text-sm text-ink-700">
        <CheckCircle2 className="size-4 text-brand-500" aria-hidden /> No errors: every test that ran passed.
      </p>
    )
  }

  const limitLine =
    failing.status === 'TIME_LIMIT_EXCEEDED' && v.timeLimitMs
      ? `Time limit: ${formatTimeLimit(v.timeLimitMs)}${failing.runtime_ms !== null ? ` · Your program ran for at least ${failing.runtime_ms} ms` : ''}`
      : failing.status === 'MEMORY_LIMIT_EXCEEDED' && v.memoryLimitKb
        ? `Memory limit: ${formatMemory(v.memoryLimitKb)}${failing.memory_kb !== null ? ` · Peak memory ${formatMemory(failing.memory_kb)}` : ''}`
        : null
  return (
    <div className="space-y-2">
      <p className="text-sm font-semibold text-danger">Failed on {testLabel(failing)}</p>
      {limitLine && <p className="font-mono text-xs text-ink-700">{limitLine}</p>}
      {failing.kind === 'hidden' ? (
        <>
          <p className="flex items-center gap-2 text-sm text-ink-500">
            <EyeOff className="size-4 shrink-0" aria-hidden /> Hidden test case: the input and expected output are hidden.
          </p>
          {!v.isRun && v.message && <OutputTerminal blocks={[{ label: 'Error', text: v.message, tone: 'error' }]} />}
        </>
      ) : (
        <OutputTerminal
          emptyText={failing.status === 'FAILED' ? 'Wrong answer: no error output. Compare your output in the Result tab.' : 'No error output.'}
          blocks={[{ label: 'Error output (stderr)', text: failing.stderr, tone: 'error' }]}
        />
      )}
    </div>
  )
}
