import { useCallback } from 'react'
import { Activity, ArrowRight, GraduationCap, ServerCog, UserCog, Users } from 'lucide-react'
import { Link } from 'react-router-dom'
import { DashboardHero } from '../../components/dashboard/DashboardHero'
import { SystemStatusPanel } from '../../components/dashboard/SystemStatusPanel'
import { Avatar } from '../../components/ui/Avatar'
import { RoleBadge, StatusBadge } from '../../components/ui/Badge'
import { ButtonLink } from '../../components/ui/Button'
import { SectionCard } from '../../components/ui/Card'
import { EmptyState } from '../../components/ui/EmptyState'
import { ErrorState } from '../../components/ui/ErrorState'
import { DashboardSkeleton } from '../../components/ui/LoadingState'
import { StatCard } from '../../components/ui/StatCard'
import { useApiQuery } from '../../hooks/useApiQuery'
import { adminService } from '../../services/adminService'
import { dashboardService } from '../../services/dashboardService'
import { formatDate } from '../../utils/format'

export default function AdminDashboard() {
  const load = useCallback(async () => {
    const [dashboard, recent] = await Promise.all([
      dashboardService.getAdminDashboard(),
      adminService.listUsers({ page: 1, pageSize: 5 }),
    ])
    return { dashboard, recentUsers: recent.items }
  }, [])
  const { data, loading, error, reload } = useApiQuery(load)

  if (loading) return <DashboardSkeleton />
  if (error || !data) {
    return <ErrorState title="Unable to load dashboard data." message={error ?? 'No data received.'} onRetry={reload} />
  }

  const { dashboard: d, recentUsers } = data
  const online = d.system_status.filter((s) => s.status === 'online').length

  return (
    <div className="animate-fade-in space-y-6">
      <DashboardHero
        eyebrow="Admin · Console"
        title="System Control"
        subtitle="Monitor the platform and manage user accounts."
        meta={[
          { label: 'Services online', value: `${online}/${d.system_status.length}` },
          { label: 'Inactive users', value: d.inactive_users },
        ]}
        action={
          <ButtonLink to="/admin/users" size="sm" iconRight={<ArrowRight className="size-4" aria-hidden />}>
            Manage Users
          </ButtonLink>
        }
      />

      <section aria-label="Statistics" className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard label="Total Users" value={d.total_users} icon={<Users />} tone="brand" caption={`${d.total_admins} admin${d.total_admins === 1 ? '' : 's'}`} />
        <StatCard label="Total Students" value={d.total_students} icon={<GraduationCap />} tone="info" />
        <StatCard label="Total Staff" value={d.total_staff} icon={<UserCog />} tone="accent" />
        <StatCard label="Active Users" value={d.active_users} icon={<Activity />} tone="warning" />
      </section>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-5">
        <SectionCard
          className="lg:col-span-2"
          title="System Status"
          description="Live service health"
          icon={<ServerCog />}
          hud
          action={
            <Link to="/admin/system" className="text-xs font-semibold text-brand-500 hover:text-brand-300">
              Details
            </Link>
          }
        >
          <SystemStatusPanel services={d.system_status} showDetail={false} />
        </SectionCard>

        <SectionCard
          className="lg:col-span-3"
          title="Recently Joined"
          description="Newest accounts on the platform"
          icon={<Users />}
          action={
            <Link to="/admin/users" className="text-xs font-semibold text-brand-500 hover:text-brand-300">
              View all
            </Link>
          }
        >
          {recentUsers.length === 0 ? (
            <EmptyState icon={<Users />} title="No users yet." />
          ) : (
            <ul className="-my-3 divide-y divide-ink-200">
              {recentUsers.map((user) => (
                <li key={user.id} className="flex items-center gap-3 py-3">
                  <Avatar name={user.full_name} muted />
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-semibold text-ink-950">{user.full_name}</p>
                    <p className="truncate text-xs text-ink-500">{user.email}</p>
                  </div>
                  <div className="hidden items-center gap-2 sm:flex">
                    <RoleBadge role={user.role} />
                    <StatusBadge active={user.is_active} />
                  </div>
                  <p className="hidden w-24 text-right font-mono text-[11px] text-ink-400 md:block">
                    {formatDate(user.created_at)}
                  </p>
                </li>
              ))}
            </ul>
          )}
        </SectionCard>
      </div>
    </div>
  )
}
