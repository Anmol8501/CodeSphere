import { BarChart3, ClipboardList, GraduationCap, Plus, School, Trophy } from 'lucide-react'
import { DashboardHero } from '../../components/dashboard/DashboardHero'
import { Badge } from '../../components/ui/Badge'
import { Button } from '../../components/ui/Button'
import { SectionCard } from '../../components/ui/Card'
import { EmptyState } from '../../components/ui/EmptyState'
import { ErrorState } from '../../components/ui/ErrorState'
import { DashboardSkeleton } from '../../components/ui/LoadingState'
import { StatCard } from '../../components/ui/StatCard'
import { useApiQuery } from '../../hooks/useApiQuery'
import { useAuth } from '../../hooks/useAuth'
import { dashboardService } from '../../services/dashboardService'
import { formatMonthYear } from '../../utils/format'

const COMING_SOON = 'Available in a future phase'

function SoonButton({ label }: { label: string }) {
  return (
    <Button variant="secondary" size="sm" icon={<Plus className="size-4" aria-hidden />} disabled title={COMING_SOON}>
      {label}
      <Badge tone="warning" mono className="ml-1">
        Soon
      </Badge>
    </Button>
  )
}

export default function StaffDashboard() {
  const { user: authUser } = useAuth()
  const { data, loading, error, reload } = useApiQuery(dashboardService.getStaffDashboard)

  if (loading) return <DashboardSkeleton />
  if (error || !data) {
    return <ErrorState title="Unable to load dashboard data." message={error ?? 'No data received.'} onRetry={reload} />
  }

  const { user, statistics } = data

  return (
    <div className="animate-fade-in space-y-6">
      <DashboardHero
        eyebrow="Staff · Control Panel"
        title={`Welcome, ${user.full_name}`}
        subtitle="Manage your classrooms and track student progress."
        meta={[
          { label: 'Role', value: user.role },
          { label: 'Member since', value: authUser ? formatMonthYear(authUser.created_at) : '-' },
        ]}
        action={
          <>
            <SoonButton label="Create Classroom" />
            <SoonButton label="Create Assignment" />
          </>
        }
      />

      <section aria-label="Statistics" className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard label="Students" value={statistics.students} icon={<GraduationCap />} tone="info" />
        <StatCard label="Classrooms" value={statistics.classrooms} icon={<School />} tone="brand" />
        <StatCard label="Assignments" value={statistics.assignments} icon={<ClipboardList />} tone="accent" />
        <StatCard label="Contests" value={statistics.contests} icon={<Trophy />} tone="warning" />
      </section>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <SectionCard title="My Classrooms" description="Classes you teach" icon={<School />}>
          <EmptyState
            icon={<School />}
            title="No classrooms created yet."
            description="Classrooms let you group students and share assignments with them."
          />
        </SectionCard>

        <SectionCard title="Recent Assignments" description="Latest work you've published" icon={<ClipboardList />}>
          <EmptyState
            icon={<ClipboardList />}
            title="No assignments created yet."
            description="Assignments you publish will appear here with their deadlines."
          />
        </SectionCard>

        <SectionCard className="lg:col-span-2" title="Student Performance" description="Progress across your classrooms" icon={<BarChart3 />}>
          <EmptyState
            icon={<BarChart3 />}
            title="No student performance data available yet."
            description="Performance insights are built from submissions once the judge engine is connected."
          />
        </SectionCard>
      </div>
    </div>
  )
}
