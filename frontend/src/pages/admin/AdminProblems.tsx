import { Archive, Code2, Eye, EyeOff, FlaskConical, Pencil, Plus } from 'lucide-react'
import { useCallback, useMemo, useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { ProblemStatusBadge } from '../../components/admin/problems/ProblemStatusBadge'
import { DifficultyBadge } from '../../components/problems/DifficultyBadge'
import { TagList } from '../../components/problems/TagList'
import { Alert } from '../../components/ui/Alert'
import { Button, ButtonLink } from '../../components/ui/Button'
import { Card } from '../../components/ui/Card'
import { EmptyState } from '../../components/ui/EmptyState'
import { TableSkeleton } from '../../components/ui/LoadingState'
import { Modal } from '../../components/ui/Modal'
import { PageHeader } from '../../components/ui/PageHeader'
import { Pagination } from '../../components/ui/Pagination'
import { SearchInput } from '../../components/ui/SearchInput'
import { Select } from '../../components/ui/Select'
import { Tabs } from '../../components/ui/Tabs'
import { useApiQuery } from '../../hooks/useApiQuery'
import { useDebouncedValue } from '../../hooks/useDebouncedValue'
import { adminProblemService } from '../../services/adminProblemService'
import { topicService } from '../../services/topicService'
import type { AdminProblemListItem } from '../../types/adminProblem'
import type { Difficulty, ProblemStatus } from '../../types/problem'
import { getErrorMessage } from '../../utils/errors'
import { cn, formatDate } from '../../utils/format'
import type { ProblemsPageNotice } from './ProblemEditorPage'

const PAGE_SIZE = 10

type StatusFilter = 'ALL' | ProblemStatus
type DifficultyFilter = 'ALL' | Difficulty

const STATUS_OPTIONS: { value: StatusFilter; label: string }[] = [
  { value: 'ALL', label: 'All' },
  { value: 'PUBLISHED', label: 'Published' },
  { value: 'DRAFT', label: 'Draft' },
  { value: 'ARCHIVED', label: 'Archived' },
]

const DIFFICULTY_OPTIONS: { value: DifficultyFilter; label: string }[] = [
  { value: 'ALL', label: 'All difficulties' },
  { value: 'EASY', label: 'Easy' },
  { value: 'MEDIUM', label: 'Medium' },
  { value: 'HARD', label: 'Hard' },
]

type Notice = { type: 'success' | 'error'; message: string }

export default function AdminProblems() {
  const location = useLocation()
  const navigate = useNavigate()
  const [notice, setNotice] = useState<Notice | null>(() => {
    const state = location.state as ProblemsPageNotice | null
    return state?.notice ? { type: 'success', message: state.notice } : null
  })
  const [search, setSearch] = useState('')
  const debouncedSearch = useDebouncedValue(search)
  const [status, setStatus] = useState<StatusFilter>('ALL')
  const [difficulty, setDifficulty] = useState<DifficultyFilter>('ALL')
  const [topic, setTopic] = useState('all')
  const [busyId, setBusyId] = useState<number | null>(null)
  const [archiveTarget, setArchiveTarget] = useState<AdminProblemListItem | null>(null)

  const topics = useApiQuery(topicService.list)
  const topicOptions = useMemo(
    () => [{ value: 'all', label: 'All topics' }, ...(topics.data ?? []).map((t) => ({ value: t.slug, label: t.name }))],
    [topics.data],
  )

  const queryKey = `${debouncedSearch.trim()}|${status}|${difficulty}|${topic}`
  const [pageState, setPageState] = useState({ key: queryKey, page: 1 })
  const page = pageState.key === queryKey ? pageState.page : 1

  const fetchProblems = useCallback(
    () =>
      adminProblemService.list({
        search: debouncedSearch,
        status: status === 'ALL' ? undefined : status,
        difficulty: difficulty === 'ALL' ? undefined : difficulty,
        topic: topic === 'all' ? undefined : topic,
        page,
        pageSize: PAGE_SIZE,
      }),
    [debouncedSearch, status, difficulty, topic, page],
  )
  const { data, loading, error, reload } = useApiQuery(fetchProblems)
  const filtered = Boolean(debouncedSearch.trim()) || status !== 'ALL' || difficulty !== 'ALL' || topic !== 'all'

  // Clear the one-time notice from history so a refresh doesn't show it again.
  const dismissNotice = () => {
    setNotice(null)
    if (location.state) navigate(location.pathname, { replace: true, state: null })
  }

  const togglePublish = async (problem: AdminProblemListItem) => {
    setBusyId(problem.id)
    try {
      const updated = await adminProblemService.setPublished(problem.id, !problem.is_published)
      setNotice({ type: 'success', message: `"${updated.title}" is now ${updated.is_published ? 'published' : 'a draft'}.` })
      reload()
    } catch (err) {
      setNotice({ type: 'error', message: getErrorMessage(err) })
    } finally {
      setBusyId(null)
    }
  }

  const confirmArchive = async () => {
    if (!archiveTarget) return
    setBusyId(archiveTarget.id)
    try {
      const archived = await adminProblemService.archive(archiveTarget.id)
      setNotice({ type: 'success', message: `"${archived.title}" was archived. Students can no longer see it.` })
      reload()
    } catch (err) {
      setNotice({ type: 'error', message: getErrorMessage(err) })
    } finally {
      setBusyId(null)
      setArchiveTarget(null)
    }
  }

  // Desktop table: icon-only actions keep each row on one line.
  // Every button keeps a full aria-label and a tooltip.
  const actions = (problem: AdminProblemListItem, compact = false) => (
    <div className={cn('flex items-center gap-1.5', compact ? 'flex-nowrap justify-end' : 'flex-wrap')}>
      <ButtonLink to={`/admin/problems/${problem.id}/edit`} size="sm" variant="secondary" icon={<Pencil className="size-3.5" aria-hidden />}
        aria-label={`Edit ${problem.title}`} title="Edit">
        {!compact && 'Edit'}
      </ButtonLink>
      <Button
        size="sm"
        variant={problem.is_published ? 'ghost' : 'success'}
        icon={problem.is_published ? <EyeOff className="size-3.5" aria-hidden /> : <Eye className="size-3.5" aria-hidden />}
        loading={busyId === problem.id}
        aria-label={`${problem.is_published ? 'Unpublish' : 'Publish'} ${problem.title}`}
        title={problem.is_published ? 'Unpublish' : 'Publish'}
        onClick={() => void togglePublish(problem)}
      >
        {!compact && (problem.is_published ? 'Unpublish' : 'Publish')}
      </Button>
      <ButtonLink to={`/admin/problems/${problem.id}/test-cases`} size="sm" variant="ghost" icon={<FlaskConical className="size-3.5" aria-hidden />}
        aria-label={`Manage test cases for ${problem.title}`} title="Manage Test Cases">
        {!compact && 'Tests'}
      </ButtonLink>
      {problem.status !== 'ARCHIVED' ? (
        <Button size="sm" variant="danger" icon={<Archive className="size-3.5" aria-hidden />} aria-label={`Archive ${problem.title}`}
          title="Archive" disabled={busyId === problem.id} onClick={() => setArchiveTarget(problem)}>
          {!compact && 'Archive'}
        </Button>
      ) : (
        compact && <span className="w-8" aria-hidden />
      )}
    </div>
  )

  return (
    <div className="animate-fade-in">
      <PageHeader
        eyebrow="Admin · Content"
        title="Problem Management"
        description="Create, edit and publish problems for the whole platform."
        action={
          <ButtonLink to="/admin/problems/new" icon={<Plus className="size-4" aria-hidden />}>
            Create Problem
          </ButtonLink>
        }
      />

      {notice && (
        <Alert variant={notice.type} className="mb-4" onDismiss={dismissNotice}>
          {notice.message}
        </Alert>
      )}

      <Card className="overflow-hidden">
        <div className="grid gap-3 border-b border-ink-200 p-4 lg:grid-cols-[minmax(0,1fr)_11rem_12rem] xl:grid-cols-[auto_minmax(0,1fr)_11rem_12rem] xl:items-end">
          <div className="lg:col-span-3 xl:col-span-1">
            <p className="mb-1.5 text-xs font-semibold text-ink-500">Status</p>
            <Tabs<StatusFilter> ariaLabel="Filter by status" size="sm" value={status} onChange={setStatus} options={STATUS_OPTIONS} />
          </div>
          <SearchInput value={search} onChange={setSearch} label="Search problems" placeholder="Search problems..." maxLength={100} />
          <Select label="Difficulty" hideLabel value={difficulty} onChange={setDifficulty} options={DIFFICULTY_OPTIONS} />
          <Select label="Topic" hideLabel value={topic} onChange={setTopic} options={topicOptions} />
        </div>

        {loading && !data ? (
          <TableSkeleton />
        ) : error ? (
          <div className="p-4">
            <Alert variant="error">Unable to load problems. {error}</Alert>
          </div>
        ) : !data || data.items.length === 0 ? (
          <div className="p-4">
            {filtered ? (
              <EmptyState icon={<Code2 />} title="No problems found." description="Try a different search term or filter." />
            ) : (
              <EmptyState icon={<Code2 />} title="No problems created yet." description="Create the first problem for your students."
                actionLabel="Create Problem" actionTo="/admin/problems/new" />
            )}
          </div>
        ) : (
          <div className={cn('transition-opacity', loading && 'opacity-60')} aria-busy={loading || undefined}>
            <div className="hidden overflow-x-auto lg:block">
              <table className="w-full text-left text-sm">
                <caption className="sr-only">Problems</caption>
                <thead className="border-b border-ink-200 bg-night/60 font-mono text-[11px] tracking-[0.14em] text-ink-400 uppercase">
                  <tr>
                    <th scope="col" className="px-4 py-3 font-semibold">Title</th>
                    <th scope="col" className="px-4 py-3 font-semibold">Topic</th>
                    <th scope="col" className="px-4 py-3 font-semibold">Difficulty</th>
                    <th scope="col" className="px-4 py-3 font-semibold">Tags</th>
                    <th scope="col" className="px-4 py-3 font-semibold">Status</th>
                    <th scope="col" className="px-4 py-3 font-semibold">Created</th>
                    <th scope="col" className="px-4 py-3 text-right font-semibold">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-ink-200">
                  {data.items.map((problem) => (
                    <tr key={problem.id} className="transition hover:bg-ink-100/50">
                      <td className="max-w-64 px-4 py-3">
                        <Link to={`/admin/problems/${problem.id}/edit`} className="font-semibold text-ink-950 hover:text-brand-400 hover:underline">
                          {problem.title}
                        </Link>
                        <p className="truncate font-mono text-[11px] text-ink-400">
                          /{problem.slug} · {problem.test_case_count} tests ({problem.hidden_test_case_count} hidden)
                        </p>
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-ink-500">{problem.topic.name}</td>
                      <td className="px-4 py-3"><DifficultyBadge difficulty={problem.difficulty} /></td>
                      <td className="px-4 py-3"><TagList tags={problem.tags} max={2} /></td>
                      <td className="px-4 py-3"><ProblemStatusBadge status={problem.status} /></td>
                      <td className="px-4 py-3 font-mono text-xs whitespace-nowrap text-ink-400">{formatDate(problem.created_at)}</td>
                      <td className="px-4 py-3">{actions(problem, true)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <ul className="divide-y divide-ink-200 lg:hidden" aria-label="Problems">
              {data.items.map((problem) => (
                <li key={problem.id} className="space-y-3 p-4">
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <Link to={`/admin/problems/${problem.id}/edit`} className="font-semibold text-ink-950 hover:text-brand-400">
                        {problem.title}
                      </Link>
                      <p className="truncate font-mono text-[11px] text-ink-400">/{problem.slug}</p>
                    </div>
                    <ProblemStatusBadge status={problem.status} />
                  </div>
                  <div className="flex flex-wrap items-center gap-2">
                    <DifficultyBadge difficulty={problem.difficulty} />
                    <span className="text-xs text-ink-500">{problem.topic.name}</span>
                    <span className="font-mono text-[11px] text-ink-400">
                      {problem.test_case_count} tests · {formatDate(problem.created_at)}
                    </span>
                  </div>
                  <TagList tags={problem.tags} max={4} />
                  {actions(problem)}
                </li>
              ))}
            </ul>
          </div>
        )}

        {data && data.total > 0 && (
          <Pagination page={page} totalPages={data.total_pages} total={data.total} noun="problem" disabled={loading}
            onChange={(next) => setPageState({ key: queryKey, page: next })} />
        )}
      </Card>

      <Modal
        open={archiveTarget !== null}
        onClose={() => busyId === null && setArchiveTarget(null)}
        title="Archive problem?"
        description={`"${archiveTarget?.title ?? ''}" will be hidden from students. You can restore it later by publishing it again.`}
        footer={
          <>
            <Button variant="secondary" onClick={() => setArchiveTarget(null)} disabled={busyId !== null}>
              Cancel
            </Button>
            <Button variant="danger" onClick={() => void confirmArchive()} loading={busyId !== null} loadingText="Archiving...">
              Archive
            </Button>
          </>
        }
      >
        <p className="text-sm text-ink-500">Archived problems keep their test cases and future submission history.</p>
      </Modal>
    </div>
  )
}
