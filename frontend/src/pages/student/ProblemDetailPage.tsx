import { ArrowLeft, BookOpen, Gauge } from 'lucide-react'
import { useCallback, type ReactNode } from 'react'
import { Link, useParams } from 'react-router-dom'
import { CodeBlock } from '../../components/problems/CodeBlock'
import { DifficultyBadge } from '../../components/problems/DifficultyBadge'
import { SolveCard } from '../../components/problems/SolveCard'
import { ProblemStatsCard, YourProgressCard } from '../../components/problems/ProblemProgressCards'
import { ProblemText } from '../../components/problems/ProblemText'
import { SolvedStatus } from '../../components/problems/SolvedStatus'
import { formatLimits } from '../../components/workspace/verdicts'
import { TagList } from '../../components/problems/TagList'
import { ButtonLink } from '../../components/ui/Button'
import { Card } from '../../components/ui/Card'
import { ErrorState } from '../../components/ui/ErrorState'
import { PageSkeleton } from '../../components/ui/LoadingState'
import { useApiQuery } from '../../hooks/useApiQuery'
import { problemService } from '../../services/problemService'

function Section({ title, children }: { title: string; children: ReactNode }) {
  const id = `problem-${title.toLowerCase().replace(/[^a-z0-9]+/g, '-')}`
  return (
    <section aria-labelledby={id} className="border-t border-ink-200 px-5 py-5 first:border-t-0 sm:px-6">
      <h2 id={id} className="mb-3 font-mono text-xs font-semibold tracking-[0.14em] text-brand-500 uppercase">
        {title}
      </h2>
      {children}
    </section>
  )
}

interface ProblemDetailPageProps {
  audience?: 'student' | 'staff'
}

export default function ProblemDetailPage({ audience = 'student' }: ProblemDetailPageProps) {
  const { slug = '' } = useParams()
  const listPath = audience === 'staff' ? '/staff/problems' : '/student/problems'
  const fetchProblem = useCallback(() => problemService.get(slug), [slug])
  const { data: problem, loading, error, reload } = useApiQuery(fetchProblem)

  const backLink = (
    <Link to={listPath} className="mb-4 inline-flex items-center gap-1.5 text-sm font-semibold text-ink-500 transition hover:text-brand-400">
      <ArrowLeft className="size-4" aria-hidden /> Back to Problems
    </Link>
  )

  if (loading && !problem) return <PageSkeleton />
  if (error || !problem) {
    return (
      <div>
        {backLink}
        <ErrorState title="Unable to load problem." message={error ?? 'No data received.'} onRetry={reload} />
      </div>
    )
  }

  return (
    <div className="animate-fade-in">
      {backLink}

      <header className="mb-6">
        <p className="mb-2 flex items-center gap-2 font-mono text-[11px] tracking-[0.18em] text-brand-500 uppercase">
          <span className="h-px w-5 bg-brand-500/60" aria-hidden />
          Problem
        </p>
        <h1 className="text-2xl font-extrabold tracking-tight text-ink-950 sm:text-[28px]">{problem.title}</h1>
        <div className="mt-3 flex flex-wrap items-center gap-3">
          <DifficultyBadge difficulty={problem.difficulty} />
          <span className="inline-flex items-center gap-1.5 text-sm text-ink-500">
            <BookOpen className="size-4" aria-hidden />
            {problem.topic.name}
          </span>
          {audience === 'student' && <SolvedStatus status={problem.user_status} showLabel />}
          <span className="inline-flex items-center gap-1.5 font-mono text-xs text-ink-500" title="Time and memory limit">
            <Gauge className="size-3.5" aria-hidden />
            {formatLimits(problem.time_limit_ms, problem.memory_limit_kb)}
          </span>
        </div>
        {problem.tags.length > 0 && <TagList tags={problem.tags} className="mt-3" />}
      </header>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-[minmax(0,1fr)_minmax(0,24rem)] lg:items-start">
        <Card as="article" aria-labelledby="problem-description" className="min-w-0">
          <Section title="Description">
            <ProblemText text={problem.description} />
          </Section>

          {problem.examples.length > 0 && (
            <Section title="Examples">
              <ol className="space-y-4">
                {problem.examples.map((example, index) => (
                  <li key={index} className="rounded-xl border border-ink-200 bg-night/40 p-4">
                    <p className="mb-3 text-sm font-semibold text-ink-950">Example {index + 1}</p>
                    <div className="space-y-3">
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
                    <code className="rounded bg-night px-2 py-1 font-mono text-[13px] text-ink-800 ring-1 ring-ink-200">{line}</code>
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

          {problem.sample_test_cases.length > 0 && (
            <Section title="Sample Tests">
              <ol className="space-y-4">
                {problem.sample_test_cases.map((test, index) => (
                  <li key={index} className="grid gap-3 sm:grid-cols-2">
                    <CodeBlock label={`Sample input ${index + 1}`} value={test.input_data} />
                    <CodeBlock label={`Sample output ${index + 1}`} value={test.expected_output} />
                  </li>
                ))}
              </ol>
            </Section>
          )}
        </Card>

        <div className="lg:sticky lg:top-20">
          <SolveCard
            languages={problem.languages}
            solvePath={audience === 'student' ? `/student/problems/${problem.slug}/solve` : undefined}
          />
          <div className="mt-4 space-y-4">
            {audience === 'student' && problem.progress && <YourProgressCard progress={problem.progress} slug={problem.slug} />}
            <ProblemStatsCard stats={problem.stats} />
          </div>
          <ButtonLink to={listPath} variant="secondary" fullWidth className="mt-4">
            Browse more problems
          </ButtonLink>
        </div>
      </div>
    </div>
  )
}
