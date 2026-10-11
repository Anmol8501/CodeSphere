import { useCallback, useState } from 'react'
import { BarChart3, RefreshCw, ServerCog } from 'lucide-react'
import { SystemStatusPanel } from '../../components/dashboard/SystemStatusPanel'
import { Button } from '../../components/ui/Button'
import { SectionCard } from '../../components/ui/Card'
import { ErrorState } from '../../components/ui/ErrorState'
import { DashboardSkeleton } from '../../components/ui/LoadingState'
import { PageHeader } from '../../components/ui/PageHeader'
import { useApiQuery } from '../../hooks/useApiQuery'
import { dashboardService } from '../../services/dashboardService'

export default function AdminSystem() {
  const [checkedAt, setCheckedAt] = useState<Date | null>(null)
  const load = useCallback(async () => {
    const result = await dashboardService.getAdminDashboard()
    setCheckedAt(new Date())
    return result
  }, [])
  const { data, loading, error, reload } = useApiQuery(load)

  if (loading && !data) return <DashboardSkeleton message="Loading system status..." />
  if (error || !data) {
    return <ErrorState title="Unable to load system status." message={error ?? 'No data received.'} onRetry={reload} />
  }

  const rows = [
    { label: 'Total users', value: data.total_users },
    { label: 'Students', value: data.total_students },
    { label: 'Staff', value: data.total_staff },
    { label: 'Admins', value: data.total_admins },
    { label: 'Active', value: data.active_users },
    { label: 'Inactive', value: data.inactive_users },
  ]

  return (
    <div className="animate-fade-in">
      <PageHeader
        eyebrow="Admin · Monitoring"
        title="System"
        description="Service health and platform overview."
        action={
          <Button variant="secondary" size="sm" icon={<RefreshCw className="size-4" aria-hidden />} onClick={reload} loading={loading}>
            Refresh
          </Button>
        }
      />

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-5">
        <SectionCard
          className="lg:col-span-3"
          title="Service Status"
          description={checkedAt ? `Last checked ${checkedAt.toLocaleTimeString()}` : 'Live health checks'}
          icon={<ServerCog />}
          hud
        >
          <SystemStatusPanel services={data.system_status} />
          <p className="mt-6 text-xs text-ink-400">
            The judge engine and AI service are not connected yet. They will report their status here once they are
            added in later phases.
          </p>
        </SectionCard>

        <SectionCard className="lg:col-span-2" title="Platform Overview" description="Counts from the database" icon={<BarChart3 />}>
          <dl className="-my-3 divide-y divide-ink-200">
            {rows.map((row) => (
              <div key={row.label} className="flex items-center justify-between py-3">
                <dt className="text-sm text-ink-500">{row.label}</dt>
                <dd className="font-mono text-sm font-semibold text-ink-950 tabular-nums">{row.value}</dd>
              </div>
            ))}
          </dl>
        </SectionCard>
      </div>
    </div>
  )
}
