import { BookOpen, ChevronDown, Gauge } from 'lucide-react'
import type { ReactNode } from 'react'
import type { Problem } from '../../types/problem'
import { CodeBlock } from '../problems/CodeBlock'
import { DifficultyBadge } from '../problems/DifficultyBadge'
import { ProblemText } from '../problems/ProblemText'
import { SolvedStatus } from '../problems/SolvedStatus'
import { TagList } from '../problems/TagList'
import { formatLimits } from './verdicts'

/** Collapsible section on native <details> (keyboard and screen-reader friendly). */
function Section({ title, children, defaultOpen = true }: { title: string; children: ReactNode; defaultOpen?: boolean }) {
  return (
    <details open={defaultOpen} className="group border-t border-ink-200 first:border-t-0">
      <summary className="flex cursor-pointer list-none items-center justify-between gap-2 px-5 py-3 font-mono text-[11px] font-semibold tracking-[0.16em] text-brand-500 uppercase transition hover:bg-ink-100/40 focus-visible:bg-ink-100/40 focus-visible:outline-none [&::-webkit-details-marker]:hidden">
        {title}
        <ChevronDown className="size-4 text-ink-400 transition group-open:rotate-180" aria-hidden />
      </summary>
      <div className="px-5 pb-5">{children}</div>
    </details>
  )
}

/**
 * Problem statement for the workspace. All text is rendered as React text
 * nodes by ProblemText (never as HTML), so stored content cannot inject markup.
 */
export function ProblemPanel({ problem, solved = false }: { problem: Problem; solved?: boolean }) {
  return (
    <article aria-labelledby="workspace-problem-title" className="h-full overflow-y-auto bg-card">
      <header className="border-b border-ink-200 px-5 py-4">
        <h1 id="workspace-problem-title" className="text-xl font-extrabold tracking-tight text-ink-950">
          {problem.title}
        </h1>
        <div className="mt-2 flex flex-wrap items-center gap-2.5">
          <DifficultyBadge difficulty={problem.difficulty} />
          <span className="inline-flex items-center gap-1.5 text-sm text-ink-500">
            <BookOpen className="size-4" aria-hidden />
            {problem.topic.name}
          </span>
          <SolvedStatus status={solved ? 'SOLVED' : problem.user_status} showLabel />
          <span className="inline-flex items-center gap-1.5 font-mono text-xs text-ink-500" title="Time and memory limit">
            <Gauge className="size-3.5" aria-hidden />
            {formatLimits(problem.time_limit_ms, problem.memory_limit_kb)}
          </span>
        </div>
        {problem.tags.length > 0 && <TagList tags={problem.tags} className="mt-3" />}
      </header>

      <Section title="Description">
        <ProblemText text={problem.description} className="text-[14px]" />
      </Section>

      {problem.examples.length > 0 && (
        <Section title="Examples">
          <ol className="space-y-3">
            {problem.examples.map((example, index) => (
              <li key={index} className="rounded-xl border border-ink-200 bg-night/40 p-3.5">
                <p className="mb-2.5 text-sm font-semibold text-ink-950">Example {index + 1}</p>
                <div className="space-y-2.5">
                  <CodeBlock label="Input" value={example.input} />
                  <CodeBlock label="Output" value={example.output} />
                  {example.explanation && (
                    <div>
                      <p className="mb-1 font-mono text-[10px] tracking-[0.2em] text-ink-400 uppercase">Explanation</p>
                      <ProblemText text={example.explanation} className="text-sm" />
                    </div>
                  )}
                </div>
              </li>
            ))}
          </ol>
        </Section>
      )}

      {problem.constraints && (
        <Section title="Constraints">
          <ul className="space-y-1.5">
            {problem.constraints.split('\n').filter(Boolean).map((line) => (
              <li key={line}>
                <code className="rounded bg-night px-2 py-1 font-mono text-[12.5px] text-ink-800 ring-1 ring-ink-200">{line}</code>
              </li>
            ))}
          </ul>
        </Section>
      )}

      {problem.input_format && (
        <Section title="Input Format">
          <ProblemText text={problem.input_format} className="text-sm" />
        </Section>
      )}

      {problem.output_format && (
        <Section title="Output Format">
          <ProblemText text={problem.output_format} className="text-sm" />
        </Section>
      )}
    </article>
  )
}
