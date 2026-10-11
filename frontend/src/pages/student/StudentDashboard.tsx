import {
  Activity,
  BarChart3,
  BookOpen,
  Bot,
  CheckCircle2,
  Code2,
  Flame,
  History,
  ListChecks,
  Rocket,
  Target,
  TrendingUp,
  Trophy,
  Zap,
} from 'lucide-react'
import { useCallback } from 'react'
import { ActivityHeatmap } from '../../components/dashboard/ActivityHeatmap'
import { DashboardHero } from '../../components/dashboard/DashboardHero'
import { QuickActions, type QuickAction } from '../../components/dashboard/QuickActions'
import { ActivityTimeline } from '../../components/progress/ActivityTimeline'
import { DifficultyProgressList } from '../../components/progress/DifficultyProgressList'
import { RecentSubmissions } from '../../components/progress/RecentSubmissions'
import { RecommendationList } from '../../components/progress/RecommendationList'
import { SectionBody } from '../../components/progress/SectionBody'
import { ButtonLink } from '../../components/ui/Button'
import { SectionCard } from '../../components/ui/Card'
import { EmptyState } from '../../components/ui/EmptyState'
import { ErrorState } from '../../components/ui/ErrorState'
import { DashboardSkeleton } from '../../components/ui/LoadingState'
import { ProgressBar } from '../../components/ui/ProgressBar'
import { StatCard } from '../../components/ui/StatCard'
import { formatPercent } from '../../components/workspace/verdicts'
import { useApiQuery } from '../../hooks/useApiQuery'
import { useAuth } from '../../hooks/useAuth'
import { dashboardService } from '../../services/dashboardService'
import { progressService } from '../../services/progressService'
import { submissionService } from '../../services/submissionService'
import { formatMonthYear, getFirstName } from '../../utils/format'

const QUICK_ACTIONS: QuickAction[] = [
  { label: 'Explore Problems', description: 'Browse the practice library.', icon: Code2, to: '/student/problems' },
  { label: 'Start Learning', description: 'Follow the DSA roadmap.', icon: BookOpen, to: '/student/learning' },
  { label: 'Leaderboard', description: 'See where you rank.', icon: BarChart3, to: '/student/leaderboard' },
  { label: 'AI Tutor', description: 'Hints and explanations.', icon: Bot, to: '/student/ai-tutor', comingSoon: true },
]

const days = (n: number) => `${n} ${n === 1 ? 'day' : 'days'}`
const fetchHeatmap = () => progressService.heatmap(365)
const fetchActivity = () => progressService.activity(8)

export default function StudentDashboard() {
  const { user: authUser } = useAuth()
  const { data, loading, error, reload } = useApiQuery(dashboardService.getStudentDashboard)
  // Independent sections: each loads (or fails) on its own.
  const heatmap = useApiQuery(fetchHeatmap)
  const activity = useApiQuery(fetchActivity)
  const fetchRecent = useCallback(() => submissionService.list({ limit: 5 }), [])
  const recent = useApiQuery(fetchRecent)

  if (loading) return <DashboardSkeleton />

  const name = data?.user.full_name ?? authUser?.full_name ?? ''
  const hero = (
    <DashboardHero
      eyebrow="Student · Dashboard"
      title={
        <>
          Welcome back, {getFirstName(name)} <span aria-hidden>👋</span>
        </>
      }
      subtitle="Ready to continue your coding journey?"
      meta={[
        { label: 'Role', value: 'STUDENT' },
        { label: 'Member since', value: authUser ? formatMonthYear(authUser.created_at) : '-' },
      ]}
    />
  )

  return (
    <div className="animate-fade-in space-y-6">
      {hero}

      {error || !data ? (
        <ErrorState title="Unable to load statistics." message={error ?? 'No data received.'} onRetry={reload} />
      ) : (
        <>
          <section aria-label="Statistics" className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5">
            <StatCard
              label="Problems Solved"
              value={data.statistics.problems_solved}
              caption={`of ${data.statistics.total_problems} problems`}
              icon={<CheckCircle2 />}
              tone="brand"
            />
            <StatCard
              label="Total Attempts"
              value={data.statistics.total_attempts}
              caption={`${data.statistics.accepted_submissions} accepted`}
              icon={<ListChecks />}
              tone="info"
            />
            <StatCard
              label="Acceptance Rate"
              value={data.statistics.total_attempts ? formatPercent(data.statistics.acceptance_rate) : '-'}
              muted={!data.statistics.total_attempts}
              caption={data.statistics.total_attempts ? 'accepted / submitted' : 'No submissions yet'}
              icon={<Target />}
              tone="accent"
            />
            <StatCard
              label="Current Streak"
              value={days(data.statistics.current_streak)}
              caption={data.statistics.active_today ? 'Active today' : data.statistics.current_streak ? 'Submit today to keep it' : 'Submit to start a streak'}
              icon={<Flame />}
              tone="warning"
            />
            <StatCard label="Longest Streak" value={days(data.statistics.longest_streak)} caption="Best run of coding days" icon={<Trophy />} tone="brand" />
          </section>

          {data.statistics.total_attempts === 0 && (
            <EmptyState
              icon={<Rocket />}
              title="Start solving your first problem."
              description="Your statistics, streak and activity update automatically after every submission."
              actionLabel="Explore Problems"
              actionTo="/student/problems"
            />
          )}

          <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
            <SectionCard title="Progress" description="Solved by difficulty" icon={<TrendingUp />}>
              <DifficultyProgressList difficulty={data.difficulty} />
            </SectionCard>
            <SectionCard className="lg:col-span-2" title="Continue Learning" description="Next steps from your progress" icon={<BookOpen />}>
              {data.continue_learning.length > 0 ? (
                <RecommendationList items={data.continue_learning} />
              ) : (
                <EmptyState
                  compact
                  icon={<Rocket />}
                  title={data.statistics.total_problems > 0 && data.statistics.problems_solved >= data.statistics.total_problems ? 'You solved every problem!' : 'No problems to recommend yet.'}
                  description="New problems will show up here as they are published."
                  actionLabel="Explore Problems"
                  actionTo="/student/problems"
                />
              )}
            </SectionCard>
          </div>
        </>
      )}

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <SectionCard title="Recent Activity" description="Your latest judged submissions" icon={<Activity />}>
          <SectionBody query={activity}>
            {(items) =>
              items.length ? (
                <ActivityTimeline items={items} linkToSubmissions />
              ) : (
                <p className="text-sm text-ink-500">No activity yet. Submit a solution and it will appear here.</p>
              )
            }
          </SectionBody>
        </SectionCard>
        <SectionCard
          title="Recent Submissions"
          description="Verdict, language and runtime"
          icon={<History />}
          action={
            <ButtonLink to="/student/submissions" variant="ghost" size="sm">
              View all
            </ButtonLink>
          }
        >
          <SectionBody query={recent}>
            {(page) =>
              page.items.length ? (
                <RecentSubmissions items={page.items} />
              ) : (
                <p className="text-sm text-ink-500">No submissions yet.</p>
              )
            }
          </SectionBody>
        </SectionCard>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <SectionCard className="min-w-0 lg:col-span-2" title="Coding Activity" description="Judged submissions per day over the last year" icon={<Zap />}>
          <SectionBody query={heatmap}>
            {(map) => (
              <>
                <ActivityHeatmap heatmap={map} />
                {map.total_submissions === 0 && (
                  <p className="mt-3 text-sm text-ink-500">Your coding activity will appear here once you start solving problems.</p>
                )}
              </>
            )}
          </SectionBody>
        </SectionCard>

        <SectionCard title="Learning Progress" description="Topic completion" icon={<TrendingUp />}>
          {data ? (
            <ul className="space-y-4">
              {data.learning_progress.map((topic) => (
                <li key={topic.slug}>
                  <ProgressBar label={`${topic.topic} (${topic.solved}/${topic.total})`} value={topic.percent} size="sm" />
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-ink-500">Unable to load statistics.</p>
          )}
        </SectionCard>
      </div>

      <SectionCard title="Quick Actions" description="Jump to a section" icon={<Zap />}>
        <QuickActions actions={QUICK_ACTIONS} />
      </SectionCard>
    </div>
  )
}
