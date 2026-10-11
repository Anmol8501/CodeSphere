import { Activity, Award, BarChart3, BookOpen, CalendarDays, CheckCircle2, Code2, Flame, Hash, ListChecks, Mail, ShieldCheck, Target, Trophy, UserRound } from 'lucide-react'
import type { ReactNode } from 'react'
import { Avatar } from '../../components/ui/Avatar'
import { RoleBadge, StatusBadge } from '../../components/ui/Badge'
import { Card, SectionCard } from '../../components/ui/Card'
import { EmptyState } from '../../components/ui/EmptyState'
import { PageHeader } from '../../components/ui/PageHeader'
import { ActivityTimeline } from '../../components/progress/ActivityTimeline'
import { LanguageStatsList, TopicProgressList } from '../../components/progress/BreakdownLists'
import { SectionBody } from '../../components/progress/SectionBody'
import { formatPercent } from '../../components/workspace/verdicts'
import { useApiQuery } from '../../hooks/useApiQuery'
import { useAuth } from '../../hooks/useAuth'
import { progressService } from '../../services/progressService'
import { formatDate } from '../../utils/format'

function DetailRow({ icon, label, children }: { icon: ReactNode; label: string; children: ReactNode }) {
  return (
    <div className="flex items-center gap-3 py-3.5">
      <span className="flex size-8 shrink-0 items-center justify-center rounded-lg bg-night text-ink-400 ring-1 ring-ink-200 [&>svg]:size-4">
        {icon}
      </span>
      <div className="min-w-0 flex-1">
        <dt className="font-mono text-[10px] tracking-[0.18em] text-ink-400 uppercase">{label}</dt>
        <dd className="truncate text-sm font-semibold text-ink-950">{children}</dd>
      </div>
    </div>
  )
}

const days = (n: number) => `${n} ${n === 1 ? 'day' : 'days'}`
const fetchProgress = () => Promise.all([progressService.overview(), progressService.streak()])
const fetchActivity = () => progressService.activity(6)

/** Coding statistics for students, computed by the server from judged submissions. */
function CodingStatistics() {
  const query = useApiQuery(fetchProgress)
  return (
    <SectionCard title="Coding Statistics" description="Updated after every submission" icon={<BarChart3 />}>
      <SectionBody query={query} rows={2}>
        {([overview, streak]) => {
          const items = [
            { label: 'Problems solved', icon: <CheckCircle2 />, value: `${overview.solved_problems} / ${overview.total_problems}` },
            { label: 'Attempts', icon: <ListChecks />, value: overview.total_submissions },
            { label: 'Acceptance rate', icon: <Target />, value: overview.total_submissions ? formatPercent(overview.acceptance_rate) : '-' },
            { label: 'Current streak', icon: <Flame />, value: days(streak.current_streak) },
            { label: 'Longest streak', icon: <Trophy />, value: days(streak.longest_streak) },
          ]
          return (
            <dl className="grid grid-cols-2 gap-3 sm:grid-cols-3">
              {items.map((item) => (
                <div key={item.label} className="rounded-xl border border-ink-200 bg-night/50 p-3">
                  <dt className="flex items-center gap-1.5 font-mono text-[10px] tracking-[0.16em] text-ink-400 uppercase [&>svg]:size-3.5">
                    {item.icon}
                    {item.label}
                  </dt>
                  <dd className="mt-1.5 text-lg font-bold text-ink-950">{item.value}</dd>
                </div>
              ))}
            </dl>
          )
        }}
      </SectionBody>
    </SectionCard>
  )
}

function StudentProgressCards() {
  const languages = useApiQuery(progressService.languages)
  const topics = useApiQuery(progressService.topics)
  const activity = useApiQuery(fetchActivity)
  return (
    <>
      <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
        <SectionCard title="Language Usage" description="Judged submissions per language" icon={<Code2 />}>
          <SectionBody query={languages}>{(rows) => <LanguageStatsList languages={rows} />}</SectionBody>
        </SectionCard>
        <SectionCard title="Topic Progress" description="Solved / published problems" icon={<BookOpen />}>
          <SectionBody query={topics}>{(rows) => <TopicProgressList topics={rows} limit={8} />}</SectionBody>
        </SectionCard>
      </div>
      <SectionCard title="Recent Activity" description="Your latest judged submissions" icon={<Activity />}>
        <SectionBody query={activity}>
          {(items) =>
            items.length ? <ActivityTimeline items={items} linkToSubmissions /> : <p className="text-sm text-ink-500">No activity yet.</p>
          }
        </SectionBody>
      </SectionCard>
    </>
  )
}

/** Profile page for every role, using real authenticated user data. */
export default function ProfilePage() {
  const { user } = useAuth()
  if (!user) return null
  const isStudent = user.role === 'STUDENT'

  return (
    <div className="animate-fade-in">
      <PageHeader eyebrow="Account · Profile" title="My Profile" description="Your CodeArena account details." />

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <Card className="overflow-hidden" hud>
          <div className="bg-dot-grid relative h-24 border-b border-ink-200 bg-night">
            <div className="absolute inset-0 bg-gradient-to-br from-brand-500/20 to-transparent" />
          </div>
          <div className="-mt-10 flex flex-col items-center px-6 pb-6 text-center">
            <Avatar name={user.full_name} size="xl" className="relative ring-4 ring-card" />
            <h2 className="mt-3 text-lg font-bold break-words text-ink-950">{user.full_name}</h2>
            <p className="max-w-full truncate text-sm text-ink-500">{user.email}</p>
            <div className="mt-3 flex items-center gap-2">
              <RoleBadge role={user.role} />
              <StatusBadge active={user.is_active} />
            </div>
          </div>
        </Card>

        <div className="space-y-6 lg:col-span-2">
          <SectionCard
            title="Profile Information"
            description="Contact your administrator to change your name or email."
            icon={<UserRound />}
          >
            <dl className="-my-3.5 divide-y divide-ink-200">
              <DetailRow icon={<UserRound />} label="Full name">{user.full_name}</DetailRow>
              <DetailRow icon={<Mail />} label="Email">{user.email}</DetailRow>
              <DetailRow icon={<ShieldCheck />} label="Role"><RoleBadge role={user.role} /></DetailRow>
              <DetailRow icon={<CalendarDays />} label="Member since">{formatDate(user.created_at)}</DetailRow>
              <DetailRow icon={<Hash />} label="User ID"><span className="font-mono">#{user.id}</span></DetailRow>
            </dl>
          </SectionCard>

          {isStudent && (
            <>
              <CodingStatistics />
              <StudentProgressCards />
              <SectionCard title="Achievements" description="Badges you earn along the way" icon={<Award />}>
                <EmptyState
                  icon={<Award />}
                  title="No achievements yet."
                  description="Solve problems and complete learning modules to earn achievements."
                />
              </SectionCard>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
