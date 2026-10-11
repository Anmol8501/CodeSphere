import { ArrowRight, BookOpen, Flag } from 'lucide-react'
import { TopicIcon } from '../../components/problems/TopicIcon'
import { Badge } from '../../components/ui/Badge'
import { ButtonLink } from '../../components/ui/Button'
import { Card } from '../../components/ui/Card'
import { EmptyState } from '../../components/ui/EmptyState'
import { ErrorState } from '../../components/ui/ErrorState'
import { PageSkeleton } from '../../components/ui/LoadingState'
import { PageHeader } from '../../components/ui/PageHeader'
import { ProgressBar } from '../../components/ui/ProgressBar'
import type { Tone } from '../../components/ui/tones'
import { useApiQuery } from '../../hooks/useApiQuery'
import { learningService } from '../../services/learningService'
import type { LearningTopic, TopicProgressStatus } from '../../types/problem'
import { cn } from '../../utils/format'

const STATUS: Record<TopicProgressStatus, { label: string; tone: Tone; action: string }> = {
  NOT_STARTED: { label: 'Not started', tone: 'neutral', action: 'Start' },
  IN_PROGRESS: { label: 'In progress', tone: 'warning', action: 'Continue' },
  COMPLETED: { label: 'Completed', tone: 'brand', action: 'Review' },
}

function TopicCard({ topic, index, highlighted }: { topic: LearningTopic; index: number; highlighted: boolean }) {
  const status = STATUS[topic.status]
  return (
    <div
      className={cn(
        'min-w-0 flex-1 rounded-xl border p-4 transition sm:p-5',
        highlighted ? 'border-brand-500/40 bg-brand-500/[0.04]' : 'border-ink-200 bg-night/40 hover:border-ink-300',
      )}
    >
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="flex min-w-0 items-center gap-3">
          <span className="flex size-9 shrink-0 items-center justify-center rounded-lg bg-surface text-brand-500 ring-1 ring-ink-200">
            <TopicIcon name={topic.icon} className="size-4" />
          </span>
          <div className="min-w-0">
            <p className="font-mono text-[10px] tracking-[0.2em] text-ink-400 uppercase">Topic {String(index + 1).padStart(2, '0')}</p>
            <h2 className="truncate font-mono text-sm font-bold tracking-wider text-ink-950 uppercase">{topic.name}</h2>
          </div>
        </div>
        <Badge tone={status.tone} mono>
          {status.label}
        </Badge>
      </div>

      <p className="mt-3 text-[13px] leading-relaxed text-ink-500">{topic.description}</p>

      <div className="mt-4 flex flex-col gap-3 sm:flex-row sm:items-end">
        <div className="min-w-0 flex-1">
          <p className="mb-1.5 font-mono text-xs text-ink-500">
            {topic.problem_count > 0
              ? `${topic.solved_count} / ${topic.problem_count} completed`
              : 'No problems published yet'}
          </p>
          <ProgressBar value={topic.progress} label={`${topic.name} progress`} hideLabel showValue={false} size="sm" />
        </div>
        <ButtonLink
          to={`/student/learning/${topic.slug}`}
          size="sm"
          variant={highlighted ? 'primary' : 'secondary'}
          iconRight={<ArrowRight className="size-3.5" aria-hidden />}
          aria-label={`${status.action} ${topic.name}`}
        >
          {status.action}
        </ButtonLink>
      </div>
    </div>
  )
}

/**
 * Learning path roadmap from the database. Every topic is open for
 * exploration (no prerequisite locking yet); the first unfinished topic that
 * has problems is highlighted as the suggested next step.
 */
export default function LearningPage() {
  const { data, loading, error, reload } = useApiQuery(learningService.getPath)

  if (loading && !data) return <PageSkeleton />
  if (error || !data) {
    return <ErrorState title="Unable to load the learning path." message={error ?? 'No data received.'} onRetry={reload} />
  }

  const { topics } = data
  const next = topics.find((t) => t.problem_count > 0 && t.status !== 'COMPLETED')
  const completed = topics.filter((t) => t.status === 'COMPLETED').length

  return (
    <div className="animate-fade-in">
      <PageHeader
        eyebrow="Module · DSA"
        title="Learning Path"
        description="Follow a structured path from programming basics to advanced DSA. Every topic is open to explore."
      />

      <dl className="mb-6 grid grid-cols-2 gap-3 lg:grid-cols-4">
        {[
          { label: 'Topics', value: String(topics.length).padStart(2, '0') },
          { label: 'Problems', value: String(data.total_problems) },
          { label: 'Solved', value: `${data.total_solved} / ${data.total_problems}` },
          { label: 'Completed topics', value: `${completed} / ${topics.length}` },
        ].map((item) => (
          <Card key={item.label} className="px-5 py-4">
            <dt className="font-mono text-[10px] tracking-[0.2em] text-ink-400 uppercase">{item.label}</dt>
            <dd className="mt-1 truncate font-mono text-lg font-semibold text-ink-950">{item.value}</dd>
          </Card>
        ))}
      </dl>

      {topics.length === 0 ? (
        <EmptyState icon={<BookOpen />} title="No learning topics available." description="Topics will appear here once they are added." />
      ) : (
        <Card className="p-4 sm:p-8">
          <ProgressBar value={data.progress} label="Overall progress" className="mx-auto mb-8 max-w-3xl" />
          <ol className="relative mx-auto max-w-3xl" aria-label="Learning roadmap">
            <li className="relative flex gap-3 pb-6 sm:gap-4">
              <span className="absolute top-10 bottom-0 left-5 w-px -translate-x-1/2 bg-gradient-to-b from-brand-500 to-brand-500/30" aria-hidden />
              <span className="relative z-10 flex size-10 shrink-0 items-center justify-center rounded-full bg-brand-500 text-night shadow-glow">
                <Flag className="size-4" aria-hidden />
              </span>
              <div className="pt-2">
                <p className="font-mono text-xs font-semibold tracking-[0.2em] text-brand-500 uppercase">Start</p>
                <p className="text-sm text-ink-500">Your path to interview-ready DSA.</p>
              </div>
            </li>

            {topics.map((topic, index) => {
              const last = index === topics.length - 1
              const highlighted = topic.id === next?.id
              const done = topic.status === 'COMPLETED'
              return (
                <li key={topic.id} className={cn('relative flex gap-3 sm:gap-4', !last && 'pb-5')}>
                  {!last && <span className="absolute top-10 bottom-0 left-5 w-px -translate-x-1/2 bg-ink-300" aria-hidden />}
                  <span
                    className={cn(
                      'relative z-10 flex size-10 shrink-0 items-center justify-center rounded-full font-mono text-xs font-bold ring-1',
                      done && 'bg-brand-500 text-night ring-brand-500',
                      !done && highlighted && 'bg-brand-500/10 text-brand-500 shadow-glow-sm ring-brand-500',
                      !done && !highlighted && 'bg-night text-ink-500 ring-ink-300',
                    )}
                    aria-hidden
                  >
                    {String(index + 1).padStart(2, '0')}
                  </span>
                  <TopicCard topic={topic} index={index} highlighted={highlighted} />
                </li>
              )
            })}
          </ol>
        </Card>
      )}
    </div>
  )
}
