import { ArrowLeft, CheckCircle2, Code2, GraduationCap, TrendingUp } from 'lucide-react'
import { useCallback, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { DIFFICULTY_LABEL, DIFFICULTY_TEXT } from '../../components/problems/labels'
import { ProblemList } from '../../components/problems/ProblemList'
import { TopicIcon } from '../../components/problems/TopicIcon'
import { Alert } from '../../components/ui/Alert'
import { Card, SectionCard } from '../../components/ui/Card'
import { EmptyState } from '../../components/ui/EmptyState'
import { ErrorState } from '../../components/ui/ErrorState'
import { PageSkeleton, TableSkeleton } from '../../components/ui/LoadingState'
import { Pagination } from '../../components/ui/Pagination'
import { ProgressBar } from '../../components/ui/ProgressBar'
import { Tabs } from '../../components/ui/Tabs'
import { useApiQuery } from '../../hooks/useApiQuery'
import { problemService } from '../../services/problemService'
import { topicService } from '../../services/topicService'
import type { Difficulty } from '../../types/problem'
import { cn } from '../../utils/format'

const PAGE_SIZE = 20
const DIFFICULTIES: Difficulty[] = ['EASY', 'MEDIUM', 'HARD']
type DifficultyFilter = 'ALL' | Difficulty

export default function TopicDetailPage() {
  const { slug = '' } = useParams()
  const [difficulty, setDifficulty] = useState<DifficultyFilter>('ALL')
  const [pageState, setPageState] = useState({ key: '', page: 1 })
  const queryKey = `${slug}|${difficulty}`
  const page = pageState.key === queryKey ? pageState.page : 1

  const fetchTopic = useCallback(() => topicService.get(slug), [slug])
  const topic = useApiQuery(fetchTopic)
  const fetchProblems = useCallback(
    () =>
      problemService.list({
        topic: slug,
        difficulty: difficulty === 'ALL' ? undefined : difficulty,
        page,
        pageSize: PAGE_SIZE,
      }),
    [slug, difficulty, page],
  )
  const problems = useApiQuery(fetchProblems)

  const backLink = (
    <Link to="/student/learning" className="mb-4 inline-flex items-center gap-1.5 text-sm font-semibold text-ink-500 transition hover:text-brand-400">
      <ArrowLeft className="size-4" aria-hidden /> Back to Learning Path
    </Link>
  )

  if (topic.loading && !topic.data) return <PageSkeleton />
  if (topic.error || !topic.data) {
    return (
      <div>
        {backLink}
        <ErrorState title="Unable to load topic." message={topic.error ?? 'No data received.'} onRetry={topic.reload} />
      </div>
    )
  }

  const data = topic.data
  const counts = data.difficulty_counts
  const tabOptions: { value: DifficultyFilter; label: string }[] = [
    { value: 'ALL', label: `All (${data.problem_count})` },
    ...DIFFICULTIES.map((d) => ({ value: d, label: `${DIFFICULTY_LABEL[d]} (${counts[d]})` })),
  ]

  return (
    <div className="animate-fade-in">
      {backLink}

      <Card className="mb-6 overflow-hidden p-6 sm:p-7" hud>
        <div className="flex flex-col gap-5 sm:flex-row sm:items-start">
          <span className="flex size-14 shrink-0 items-center justify-center rounded-2xl bg-brand-500/10 text-brand-500 ring-1 ring-brand-500/25">
            <TopicIcon name={data.icon} className="size-7" />
          </span>
          <div className="min-w-0 flex-1">
            <p className="font-mono text-[11px] tracking-[0.18em] text-brand-500 uppercase">
              Topic {String(data.order_index).padStart(2, '0')} · Learning Path
            </p>
            <h1 className="mt-1 font-mono text-2xl font-extrabold tracking-wider text-ink-950 uppercase sm:text-[28px]">{data.name}</h1>
            <p className="mt-2 max-w-2xl text-sm text-ink-500 sm:text-[15px]">{data.description}</p>
          </div>
        </div>
      </Card>

      <div className="mb-6 grid grid-cols-1 gap-6 lg:grid-cols-3">
        <SectionCard className="lg:col-span-2" title="What you will learn" icon={<GraduationCap />}>
          {data.learning_outcomes.length > 0 ? (
            <ul className="grid gap-2.5 sm:grid-cols-2">
              {data.learning_outcomes.map((outcome) => (
                <li key={outcome} className="flex items-start gap-2.5 text-sm text-ink-800">
                  <CheckCircle2 className="mt-0.5 size-4 shrink-0 text-brand-500" aria-hidden />
                  {outcome}
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-ink-500">Learning outcomes for this topic have not been added yet.</p>
          )}
        </SectionCard>

        <SectionCard title="Progress" icon={<TrendingUp />}>
          <ProgressBar value={data.progress} label={`${data.solved_count} / ${data.problem_count} solved`} />
          <dl className="mt-5 grid grid-cols-3 gap-2 text-center">
            {DIFFICULTIES.map((d) => (
              <div key={d} className="rounded-lg bg-night/60 px-2 py-2.5 ring-1 ring-ink-200">
                <dt className={cn('font-mono text-[10px] font-bold tracking-wider uppercase', DIFFICULTY_TEXT[d])}>{d}</dt>
                <dd className="mt-0.5 font-mono text-lg font-semibold text-ink-950">{counts[d]}</dd>
              </div>
            ))}
          </dl>
          {data.problem_count > 0 && data.solved_count === 0 && (
            <p className="mt-4 text-xs text-ink-400">Problems count as solved once you submit an accepted solution.</p>
          )}
        </SectionCard>
      </div>

      <Card as="section" aria-labelledby="topic-problems" className="overflow-hidden">
        <div className="flex flex-col gap-3 border-b border-ink-200 p-4 sm:flex-row sm:items-center sm:justify-between">
          <h2 id="topic-problems" className="font-mono text-xs font-semibold tracking-[0.14em] text-ink-950 uppercase">
            Problems
          </h2>
          <Tabs<DifficultyFilter> ariaLabel="Filter by difficulty" size="sm" value={difficulty} onChange={setDifficulty} options={tabOptions} />
        </div>

        {problems.loading && !problems.data ? (
          <TableSkeleton rows={4} />
        ) : problems.error ? (
          <div className="p-4">
            <Alert variant="error">Unable to load problems. {problems.error}</Alert>
          </div>
        ) : !problems.data || problems.data.items.length === 0 ? (
          <div className="p-4">
            <EmptyState
              icon={<Code2 />}
              title="No problems found."
              description={
                difficulty === 'ALL'
                  ? 'Problems for this topic will appear here once they are published.'
                  : 'No problems at this difficulty yet.'
              }
            />
          </div>
        ) : (
          <div className={cn('transition-opacity', problems.loading && 'opacity-60')} aria-busy={problems.loading || undefined}>
            <ProblemList problems={problems.data.items} basePath="/student/problems" showTopic={false} caption={`${data.name} problems`} />
          </div>
        )}

        {problems.data && problems.data.total > PAGE_SIZE && (
          <Pagination
            page={page}
            totalPages={problems.data.total_pages}
            total={problems.data.total}
            noun="problem"
            disabled={problems.loading}
            onChange={(next) => setPageState({ key: queryKey, page: next })}
          />
        )}
      </Card>
    </div>
  )
}
