import { AlertTriangle, ClipboardCheck, Code2, FlaskConical, History, Plus, Terminal, Trash2 } from 'lucide-react'
import { useState } from 'react'
import type { SampleTestCase } from '../../types/problem'
import type { CustomTestCase, SubmissionSummary } from '../../types/workspace'
import { cn } from '../../utils/format'
import { CodeBlock } from '../problems/CodeBlock'
import { LazyCodeViewer } from '../submissions/LazyCodeViewer'
import { Button } from '../ui/Button'
import { Tabs } from '../ui/Tabs'
import { TextArea } from '../ui/TextArea'
import { ErrorView } from './results/ErrorView'
import { OutputTerminal } from './results/OutputTerminal'
import { ProblemSubmissions } from './results/ProblemSubmissions'
import { testLabel, viewOf, type WorkspaceOutcome } from './results/outcome'
import { BusyState, ResultView } from './results/ResultView'
import { buildCases } from './testCases'
import { isTestPassing } from './verdicts'

export type PanelTab = 'tests' | 'result' | 'output' | 'error' | 'code' | 'submissions'

interface TestCasePanelProps {
  /** Public sample tests only; hidden tests never reach the browser. */
  samples: SampleTestCase[]
  customCases: CustomTestCase[]
  onAddCustom: (input: string, expected: string) => void
  onRemoveCustom: (id: string) => void
  selectedCaseId: string | null
  onSelectCase: (id: string) => void
  tab: PanelTab
  onTabChange: (tab: PanelTab) => void
  outcome: WorkspaceOutcome | null
  busy: 'run' | 'submit' | null
  onRetry: () => void
  submissions: { items: SubmissionSummary[] | null; loading: boolean; error: string | null }
  problemSlug: string
}

export function TestCasePanel({
  samples,
  customCases,
  onAddCustom,
  onRemoveCustom,
  selectedCaseId,
  onSelectCase,
  tab,
  onTabChange,
  outcome,
  busy,
  onRetry,
  submissions,
  problemSlug,
}: TestCasePanelProps) {
  const [adding, setAdding] = useState(false)
  const [input, setInput] = useState('')
  const [expected, setExpected] = useState('')
  const cases = buildCases(samples, customCases)
  const selected = cases.find((c) => c.id === selectedCaseId) ?? cases[0] ?? null
  const isCustom = selected ? customCases.some((c) => c.id === selected.id) : false

  const view = outcome ? viewOf(outcome) : null
  const results = view?.tests ?? []
  // Output shows the first failing test (or the first test) of the last run/submission.
  const shown = results.find((t) => !isTestPassing(t.status)) ?? results[0]
  const compileText = view?.compileText ?? null

  const addCase = () => {
    onAddCustom(input, expected)
    setInput('')
    setExpected('')
    setAdding(false)
  }

  return (
    <section aria-label="Test cases and results" className="flex h-full min-h-0 flex-col bg-card">
      <div className="flex items-center justify-between gap-2 overflow-x-auto border-b border-ink-200 px-3 py-2">
        <Tabs<PanelTab>
          ariaLabel="Test panel"
          size="sm"
          value={tab}
          onChange={onTabChange}
          options={[
            { value: 'tests', label: 'Test Cases', icon: <FlaskConical className="size-3.5" aria-hidden /> },
            { value: 'result', label: 'Result', icon: <ClipboardCheck className="size-3.5" aria-hidden /> },
            { value: 'output', label: 'Output', icon: <Terminal className="size-3.5" aria-hidden /> },
            { value: 'error', label: 'Error', icon: <AlertTriangle className="size-3.5" aria-hidden /> },
            { value: 'code', label: 'Code', icon: <Code2 className="size-3.5" aria-hidden /> },
            { value: 'submissions', label: 'Submissions', icon: <History className="size-3.5" aria-hidden /> },
          ]}
        />
      </div>

      <div className="min-h-0 flex-1 overflow-y-auto p-3">
        {tab === 'tests' && (
          <div className="space-y-3">
            <div className="flex flex-wrap items-center gap-1.5" role="group" aria-label="Choose a test case">
              {cases.map((c) => (
                <button
                  key={c.id}
                  type="button"
                  aria-pressed={selected?.id === c.id}
                  onClick={() => onSelectCase(c.id)}
                  className={cn(
                    'rounded-lg px-2.5 py-1 font-mono text-xs font-semibold ring-1 transition',
                    selected?.id === c.id ? 'bg-brand-500/10 text-brand-400 ring-brand-500/40' : 'bg-night text-ink-500 ring-ink-200 hover:text-ink-900',
                  )}
                >
                  {c.label}
                </button>
              ))}
              <Button size="sm" variant="ghost" icon={<Plus className="size-3.5" aria-hidden />} onClick={() => setAdding(true)} disabled={adding}>
                Custom Test Case
              </Button>
            </div>

            {adding && (
              <div className="space-y-2.5 rounded-xl border border-ink-200 bg-night/40 p-3" role="group" aria-label="New custom test case">
                <div className="grid gap-2.5 sm:grid-cols-2">
                  <TextArea label="Custom input" mono rows={3} value={input} maxLength={100000} onChange={(e) => setInput(e.target.value)} />
                  <TextArea label="Expected output (optional)" mono rows={3} value={expected} maxLength={100000} onChange={(e) => setExpected(e.target.value)} />
                </div>
                <p className="text-xs text-ink-400">
                  Custom cases stay in this browser. Run executes them too, but they never count toward your official result.
                </p>
                <div className="flex justify-end gap-2">
                  <Button size="sm" variant="secondary" onClick={() => setAdding(false)}>
                    Cancel
                  </Button>
                  <Button size="sm" onClick={addCase} disabled={!input.trim()}>
                    Add case
                  </Button>
                </div>
              </div>
            )}

            {selected ? (
              <div className="space-y-2.5">
                <div className="grid gap-2.5 sm:grid-cols-2">
                  <CodeBlock label="Input" value={selected.input} />
                  <CodeBlock label="Expected output" value={selected.expected || '(not specified)'} />
                </div>
                {isCustom && (
                  <Button size="sm" variant="ghost" icon={<Trash2 className="size-3.5" aria-hidden />} onClick={() => onRemoveCustom(selected.id)}>
                    Remove {selected.label}
                  </Button>
                )}
              </div>
            ) : (
              !adding && <p className="text-sm text-ink-500">This problem has no public sample tests. Add a custom test case to try your own input.</p>
            )}
          </div>
        )}

        {tab === 'result' && <ResultView outcome={outcome} busy={busy} onRetry={onRetry} />}

        {tab === 'error' && <ErrorView outcome={outcome} busy={busy} />}

        {tab === 'code' &&
          (busy ? (
            <BusyState busy={busy} />
          ) : outcome ? (
            <div className="space-y-2">
              <p className="text-xs text-ink-500">
                The exact {outcome.languageLabel} code that was {outcome.mode === 'run' ? 'run' : 'submitted'}
                {view?.submissionId ? ` (Submission #${view.submissionId})` : ''}.
              </p>
              <LazyCodeViewer
                key={`${outcome.mode}-${view?.submissionId ?? outcome.sourceCode.length}`}
                code={outcome.sourceCode}
                language={outcome.language}
                modelId={`workspace-last-${outcome.mode}-${view?.submissionId ?? 'run'}`}
                maxHeight={360}
              />
            </div>
          ) : (
            <p className="font-mono text-xs text-ink-400">Run or submit your code to see the exact code that was judged.</p>
          ))}

        {tab === 'output' &&
          (busy ? (
            <BusyState busy={busy} />
          ) : compileText ? (
            <OutputTerminal blocks={[{ label: 'Compiler output', text: compileText, tone: 'error' }]} />
          ) : !shown ? (
            <p className="font-mono text-xs text-ink-400">Run your code to see its output here.</p>
          ) : shown.kind === 'hidden' ? (
            <p className="text-sm text-ink-500">Output on hidden tests is not shown. Your public test results are in the Result tab.</p>
          ) : (
            <div className="space-y-2">
              <p className="font-mono text-[11px] text-ink-400">{testLabel(shown)}</p>
              <OutputTerminal
                blocks={[
                  { label: 'stdout', text: shown.actual_output },
                  { label: 'stderr', text: shown.stderr, tone: 'error' },
                ]}
              />
            </div>
          ))}

        {tab === 'submissions' && (
          <ProblemSubmissions submissions={submissions.items} loading={submissions.loading} error={submissions.error} problemSlug={problemSlug} />
        )}
      </div>
    </section>
  )
}
