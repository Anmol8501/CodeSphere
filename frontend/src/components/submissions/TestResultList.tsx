import { CircleDashed, EyeOff } from 'lucide-react'
import { useState } from 'react'
import type { TestResult } from '../../types/workspace'
import { cn } from '../../utils/format'
import { OutputTerminal } from '../workspace/results/OutputTerminal'
import { testKey, testLabel } from '../workspace/results/outcome'
import { formatMemory, formatRuntime, isTestPassing } from '../workspace/verdicts'
import { TestStatusBadge } from './VerdictBadge'

interface TestResultListProps {
  tests: TestResult[]
  /** Official tests not executed because judging stops at the first failure. */
  notRun?: number
}

/**
 * Per-test results: ✓ / ✗ / not run, with details for the selected test.
 * Public tests show input, expected and actual output. Hidden tests show only
 * their status (the server never sends their data).
 */
export function TestResultList({ tests, notRun = 0 }: TestResultListProps) {
  const [selectedKey, setSelectedKey] = useState<string | null>(null)
  const selected =
    tests.find((t) => testKey(t) === selectedKey) ?? tests.find((t) => !isTestPassing(t.status)) ?? tests[0] ?? null
  const lastOfficial = tests.filter((t) => t.kind !== 'custom').reduce((max, t) => Math.max(max, t.index), 0)
  const notRunIndexes = Array.from({ length: notRun }, (_, i) => lastOfficial + i + 1)

  if (tests.length === 0 && notRun === 0) return null
  return (
    <div className="space-y-2">
      <div className="grid gap-3 md:grid-cols-[12rem_minmax(0,1fr)]">
        <ul className="flex flex-wrap gap-1.5 md:flex-col" aria-label="Test results">
          {tests.map((t) => {
            const key = testKey(t)
            const ok = isTestPassing(t.status)
            const active = selected ? testKey(selected) === key : false
            return (
              <li key={key}>
                <button
                  type="button"
                  aria-pressed={active}
                  onClick={() => setSelectedKey(key)}
                  className={cn(
                    'flex w-full items-center gap-2 rounded-lg px-2.5 py-1.5 text-left font-mono text-xs ring-1 transition',
                    active ? 'bg-ink-100 ring-brand-500/40' : 'bg-night ring-ink-200 hover:ring-ink-300',
                  )}
                >
                  <span className={cn('font-bold', ok ? 'text-brand-500' : 'text-danger')} aria-hidden>
                    {ok ? '✓' : '✗'}
                  </span>
                  <span className="truncate text-ink-900">{testLabel(t)}</span>
                  {t.kind === 'hidden' && <EyeOff className="size-3 shrink-0 text-ink-400" aria-label="hidden test" />}
                  <span className="sr-only">{ok ? 'passed' : 'failed'}</span>
                </button>
              </li>
            )
          })}
          {notRunIndexes.map((index) => (
            <li key={`not-run-${index}`}>
              <span
                className="flex w-full items-center gap-2 rounded-lg bg-night/40 px-2.5 py-1.5 font-mono text-xs text-ink-400 ring-1 ring-ink-200"
                title="Not run: judging stops at the first failing test"
              >
                <CircleDashed className="size-3.5 shrink-0" aria-hidden />
                <span className="truncate">Test Case {index}</span>
                <span className="sr-only">not run</span>
              </span>
            </li>
          ))}
        </ul>
        {selected && <TestDetail test={selected} />}
      </div>
      {notRun > 0 && (
        <p className="text-xs text-ink-400">
          {notRun} test case{notRun === 1 ? ' was' : 's were'} not run: judging stops at the first failing test.
        </p>
      )}
    </div>
  )
}

function TestDetail({ test }: { test: TestResult }) {
  const ok = isTestPassing(test.status)
  return (
    <div className="min-w-0 space-y-2.5">
      <div className="flex flex-wrap items-center gap-2">
        <p className="text-sm font-semibold text-ink-950">{testLabel(test)}</p>
        <TestStatusBadge status={test.status} />
        <span className="font-mono text-[11px] text-ink-400">
          {formatRuntime(test.runtime_ms)} · {formatMemory(test.memory_kb)}
        </span>
      </div>
      {test.kind === 'hidden' ? (
        <p className="flex items-center gap-2 rounded-lg bg-night/60 px-3 py-2.5 text-sm text-ink-500 ring-1 ring-ink-200">
          <EyeOff className="size-4 shrink-0" aria-hidden />
          Hidden test case{ok ? '' : ' failed'}: the input and expected output are hidden.
        </p>
      ) : (
        <OutputTerminal
          blocks={[
            { label: 'Input', text: test.input },
            { label: 'Expected output', text: test.expected_output },
            { label: 'Your output', text: test.actual_output, tone: ok ? 'default' : 'error' },
            { label: 'Error output (stderr)', text: test.stderr, tone: 'error' },
          ]}
        />
      )}
    </div>
  )
}
