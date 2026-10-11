import { ChevronLeft, ChevronRight, UserPlus, Users } from 'lucide-react'
import { useCallback, useState } from 'react'
import { CreateStaffModal } from '../../components/admin/CreateStaffModal'
import { Alert } from '../../components/ui/Alert'
import { Avatar } from '../../components/ui/Avatar'
import { RoleBadge, StatusBadge } from '../../components/ui/Badge'
import { Button } from '../../components/ui/Button'
import { Card } from '../../components/ui/Card'
import { EmptyState } from '../../components/ui/EmptyState'
import { TableSkeleton } from '../../components/ui/LoadingState'
import { Modal } from '../../components/ui/Modal'
import { PageHeader } from '../../components/ui/PageHeader'
import { SearchInput } from '../../components/ui/SearchInput'
import { Tabs } from '../../components/ui/Tabs'
import { useApiQuery } from '../../hooks/useApiQuery'
import { useAuth } from '../../hooks/useAuth'
import { useDebouncedValue } from '../../hooks/useDebouncedValue'
import { adminService } from '../../services/adminService'
import type { Role, User } from '../../types/auth'
import { getErrorMessage } from '../../utils/errors'
import { cn, formatDate } from '../../utils/format'

const PAGE_SIZE = 10

type RoleFilter = 'ALL' | Role
type StatusFilter = 'all' | 'active' | 'inactive'

const ROLE_OPTIONS: { value: RoleFilter; label: string }[] = [
  { value: 'ALL', label: 'All' },
  { value: 'STUDENT', label: 'Students' },
  { value: 'STAFF', label: 'Staff' },
  { value: 'ADMIN', label: 'Admin' },
]

const STATUS_OPTIONS: { value: StatusFilter; label: string }[] = [
  { value: 'all', label: 'Any status' },
  { value: 'active', label: 'Active' },
  { value: 'inactive', label: 'Inactive' },
]

const HEADINGS: Record<'ALL' | 'STUDENT' | 'STAFF', { eyebrow: string; title: string; description: string }> = {
  ALL: { eyebrow: 'Admin · Accounts', title: 'User Management', description: 'View, search and manage every account on CodeArena.' },
  STUDENT: { eyebrow: 'Admin · Accounts', title: 'Students', description: 'All registered student accounts.' },
  STAFF: { eyebrow: 'Admin · Accounts', title: 'Staff', description: 'Staff accounts created by administrators.' },
}

interface AdminUsersProps {
  /** Fixes the role filter (used by /admin/students and /admin/staff). */
  lockedRole?: 'STUDENT' | 'STAFF'
}

export default function AdminUsers({ lockedRole }: AdminUsersProps) {
  const { user: currentUser } = useAuth()
  const [roleFilter, setRoleFilter] = useState<RoleFilter>('ALL')
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('all')
  const [search, setSearch] = useState('')
  const debouncedSearch = useDebouncedValue(search)
  const [notice, setNotice] = useState<{ type: 'success' | 'error'; message: string } | null>(null)
  const [pendingUser, setPendingUser] = useState<User | null>(null)
  const [updating, setUpdating] = useState(false)
  const [createOpen, setCreateOpen] = useState(false)

  const role: Role | undefined = lockedRole ?? (roleFilter === 'ALL' ? undefined : roleFilter)
  const isActive = statusFilter === 'all' ? undefined : statusFilter === 'active'
  const heading = HEADINGS[lockedRole ?? 'ALL']

  // Page number is remembered per filter combination, so changing any filter
  // automatically returns to page 1.
  const queryKey = `${role ?? 'ALL'}|${statusFilter}|${debouncedSearch.trim()}`
  const [pageState, setPageState] = useState({ key: queryKey, page: 1 })
  const page = pageState.key === queryKey ? pageState.page : 1
  const setPage = (next: number) => setPageState({ key: queryKey, page: next })

  const fetchUsers = useCallback(
    () => adminService.listUsers({ role, isActive, search: debouncedSearch, page, pageSize: PAGE_SIZE }),
    [role, isActive, debouncedSearch, page],
  )
  const { data, loading, error, reload } = useApiQuery(fetchUsers)
  const totalPages = data ? Math.max(1, Math.ceil(data.total / PAGE_SIZE)) : 1

  const confirmStatusChange = async () => {
    if (!pendingUser) return
    setUpdating(true)
    try {
      const updated = await adminService.setUserStatus(pendingUser.id, !pendingUser.is_active)
      setNotice({
        type: 'success',
        message: `${updated.full_name} has been ${updated.is_active ? 'activated' : 'deactivated'}.`,
      })
      reload()
    } catch (err) {
      setNotice({ type: 'error', message: getErrorMessage(err) })
    } finally {
      setUpdating(false)
      setPendingUser(null)
    }
  }

  const renderAction = (user: User) => {
    const isSelf = user.id === currentUser?.id
    return (
      <Button
        size="sm"
        variant={user.is_active ? 'danger' : 'success'}
        disabled={isSelf}
        title={isSelf ? 'You cannot deactivate your own account' : undefined}
        aria-label={`${user.is_active ? 'Deactivate' : 'Activate'} ${user.full_name}`}
        onClick={() => setPendingUser(user)}
      >
        {user.is_active ? 'Deactivate' : 'Activate'}
      </Button>
    )
  }

  const canAddStaff = lockedRole !== 'STUDENT'

  return (
    <div className="animate-fade-in">
      <PageHeader
        eyebrow={heading.eyebrow}
        title={heading.title}
        description={heading.description}
        action={
          canAddStaff && (
            <Button icon={<UserPlus className="size-4" aria-hidden />} onClick={() => setCreateOpen(true)}>
              Add Staff
            </Button>
          )
        }
      />

      {notice && (
        <Alert variant={notice.type} className="mb-4" onDismiss={() => setNotice(null)}>
          {notice.message}
        </Alert>
      )}

      <Card className="overflow-hidden">
        {/* Filters */}
        <div className="flex flex-col gap-3 border-b border-ink-200 p-4 xl:flex-row xl:items-center xl:justify-between">
          <div className="flex flex-wrap gap-2">
            {!lockedRole && (
              <Tabs<RoleFilter> ariaLabel="Filter by role" value={roleFilter} onChange={setRoleFilter} options={ROLE_OPTIONS} />
            )}
            <Tabs<StatusFilter> ariaLabel="Filter by status" value={statusFilter} onChange={setStatusFilter} options={STATUS_OPTIONS} />
          </div>
          <SearchInput
            className="w-full xl:w-72"
            value={search}
            onChange={setSearch}
            label="Search users by name or email"
            placeholder="Search name or email"
          />
        </div>

        {/* Content */}
        {loading && !data ? (
          <TableSkeleton />
        ) : error ? (
          <div className="p-4">
            <Alert variant="error">{error}</Alert>
          </div>
        ) : !data || data.items.length === 0 ? (
          <div className="p-4">
            <EmptyState
              icon={<Users />}
              title="No users found."
              description={debouncedSearch || statusFilter !== 'all' ? 'Try a different search term or filter.' : undefined}
            />
          </div>
        ) : (
          <div className={cn('transition-opacity', loading && 'opacity-60')} aria-busy={loading || undefined}>
            {/* Desktop table (scrolls inside its container if needed) */}
            <div className="hidden overflow-x-auto md:block">
              <table className="w-full text-left text-sm">
                <caption className="sr-only">{heading.title}</caption>
                <thead className="border-b border-ink-200 bg-night/60 font-mono text-[11px] tracking-[0.14em] text-ink-400 uppercase">
                  <tr>
                    <th scope="col" className="px-4 py-3 font-semibold">Name</th>
                    <th scope="col" className="px-4 py-3 font-semibold">Email</th>
                    <th scope="col" className="px-4 py-3 font-semibold">Role</th>
                    <th scope="col" className="px-4 py-3 font-semibold">Status</th>
                    <th scope="col" className="px-4 py-3 font-semibold">Created</th>
                    <th scope="col" className="px-4 py-3 text-right font-semibold">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-ink-200">
                  {data.items.map((user) => (
                    <tr key={user.id} className="transition hover:bg-ink-100/50">
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2.5">
                          <Avatar name={user.full_name} size="sm" muted />
                          <span className="font-semibold text-ink-950">
                            {user.full_name}
                            {user.id === currentUser?.id && (
                              <span className="ml-1.5 text-xs font-medium text-ink-400">(you)</span>
                            )}
                          </span>
                        </div>
                      </td>
                      <td className="px-4 py-3 text-ink-500">{user.email}</td>
                      <td className="px-4 py-3"><RoleBadge role={user.role} /></td>
                      <td className="px-4 py-3"><StatusBadge active={user.is_active} /></td>
                      <td className="px-4 py-3 font-mono text-xs whitespace-nowrap text-ink-400">{formatDate(user.created_at)}</td>
                      <td className="px-4 py-3 text-right">{renderAction(user)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Mobile cards */}
            <ul className="divide-y divide-ink-200 md:hidden">
              {data.items.map((user) => (
                <li key={user.id} className="space-y-3 p-4">
                  <div className="flex items-start gap-3">
                    <Avatar name={user.full_name} size="sm" muted />
                    <div className="min-w-0">
                      <p className="truncate font-semibold text-ink-950">
                        {user.full_name}
                        {user.id === currentUser?.id && <span className="ml-1 text-xs text-ink-400">(you)</span>}
                      </p>
                      <p className="truncate text-sm text-ink-500">{user.email}</p>
                    </div>
                  </div>
                  <div className="flex flex-wrap items-center gap-2">
                    <RoleBadge role={user.role} />
                    <StatusBadge active={user.is_active} />
                    <span className="font-mono text-[11px] text-ink-400">Joined {formatDate(user.created_at)}</span>
                  </div>
                  {renderAction(user)}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Pagination */}
        {data && data.total > 0 && (
          <div className="flex flex-wrap items-center justify-between gap-3 border-t border-ink-200 px-4 py-3 text-sm text-ink-500">
            <p className="font-mono text-xs">
              {data.total} user{data.total === 1 ? '' : 's'} · Page {page} of {totalPages}
            </p>
            <div className="flex gap-2">
              <Button
                size="sm"
                variant="secondary"
                icon={<ChevronLeft className="size-4" aria-hidden />}
                disabled={page <= 1 || loading}
                onClick={() => setPage(page - 1)}
              >
                Prev
              </Button>
              <Button size="sm" variant="secondary" disabled={page >= totalPages || loading} onClick={() => setPage(page + 1)}>
                Next <ChevronRight className="size-4" aria-hidden />
              </Button>
            </div>
          </div>
        )}
      </Card>

      <Modal
        open={pendingUser !== null}
        onClose={() => !updating && setPendingUser(null)}
        title={pendingUser?.is_active ? 'Deactivate user?' : 'Activate user?'}
        description={
          pendingUser?.is_active
            ? `${pendingUser.full_name} will be signed out and won't be able to log in until reactivated.`
            : `${pendingUser?.full_name ?? 'This user'} will be able to log in again.`
        }
        footer={
          <>
            <Button variant="secondary" onClick={() => setPendingUser(null)} disabled={updating}>
              Cancel
            </Button>
            <Button
              variant={pendingUser?.is_active ? 'danger' : 'primary'}
              onClick={confirmStatusChange}
              loading={updating}
              loadingText="Saving..."
            >
              {pendingUser?.is_active ? 'Deactivate' : 'Activate'}
            </Button>
          </>
        }
      >
        {pendingUser && (
          <div className="flex items-center gap-3 rounded-xl bg-night p-3 ring-1 ring-ink-200">
            <Avatar name={pendingUser.full_name} muted />
            <div className="min-w-0">
              <p className="truncate text-sm font-semibold text-ink-950">{pendingUser.full_name}</p>
              <p className="truncate text-xs text-ink-500">{pendingUser.email}</p>
            </div>
            <span className="ml-auto">
              <RoleBadge role={pendingUser.role} />
            </span>
          </div>
        )}
      </Modal>

      <CreateStaffModal
        open={createOpen}
        onClose={() => setCreateOpen(false)}
        onCreated={(user) => {
          setCreateOpen(false)
          setNotice({ type: 'success', message: `Staff account created for ${user.full_name} (${user.email}).` })
          reload()
        }}
      />
    </div>
  )
}
