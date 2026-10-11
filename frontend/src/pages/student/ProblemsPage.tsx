import { Code2, Filter, RefreshCw } from 'lucide-react'
import { useCallback, useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { ProblemList } from '../../components/problems/ProblemList'
import { Alert } from '../../components/ui/Alert'
import { Button } from '../../components/ui/Button'
import { Card } from '../../components/ui/Card'
import { EmptyState } from '../../components/ui/EmptyState'
import { TableSkeleton } from '../../components/ui/LoadingState'
import { PageHeader } from '../../components/ui/PageHeader'
import { Pagination } from '../../components/ui/Pagination'
import { SearchInput } from '../../components/ui/SearchInput'
import { Select } from '../../components/ui/Select'
import { Tabs } from '../../components/ui/Tabs'
import { useApiQuery } from '../../hooks/useApiQuery'
import { useDebouncedValue } from '../../hooks/useDebouncedValue'
import { problemService } from '../../services/problemService'
import { topicService } from '../../services/topicService'
import type { Difficulty, ProgressFilter } from '../../types/problem'
import { cn } from '../../utils/format'

const PAGE_SIZE = 20

type DifficultyFilter = 'ALL' | Difficulty
type StatusFilter = 'all' | ProgressFilter

const DIFFICULTY_OPTIONS: { value: DifficultyFilter; label: string }[] = [
  { value: 'ALL', label: 'All' },
  { value: 'EASY', label: 'Easy' },
  { value: 'MEDIUM', label: 'Medium' },
  { value: 'HARD', label: 'Hard' },
]

const STATUS_OPTIONS: { value: StatusFilter; label: string }[] = [
  { value: 'all', label: 'All' },
  { value: 'solved', label: 'Solved' },
  { value: 'attempted', label: 'Attempted' },
  { value: 'unsolved', label: 'Unsolved' },
]

interface ProblemsPageProps {
  /** Staff get a read-only library without personal progress. */
  audience?: 'student' | 'staff'
}

export default function ProblemsPage({ audience = 'student' }: ProblemsPageProps) {
  const isStaff = audience === 'staff'
  const basePath = isStaff ? '/staff/problems' : '/student/problems'
  const [searchParams] = useSearchParams()

  const [search, setSearch] = useState('')
  const debouncedSearch = useDebouncedValue(search)
  const [difficulty, setDifficulty] = useState<DifficultyFilter>('ALL')
  const [topic, setTopic] = useState(() => searchParams.get('topic') ?? 'all')
  const [tag, setTag] = useState('all')
  const [status, setStatus] = useState<StatusFilter>('all')

  // Filter options come from the database too.
  const topics = useApiQuery(topicService.list)
  const tags = useApiQuery(problemService.listTags)
  const topicOptions = useMemo(
    () => [{ value: 'all', label: 'All Topics' }, ...(topics.data ?? []).map((t) => ({ value: t.slug, label: t.name }))],
    [topics.data],
  )
  const tagOptions = useMemo(
    () => [{ value: 'all', label: 'All Tags' }, ...(tags.data ?? []).map((t) => ({ value: t.slug, label: t.name }))],
    [tags.data],
  )

  // Changing any filter returns to page 1.
  const queryKey = `${debouncedSearch.trim()}|${difficulty}|${topic}|${tag}|${status}`
  const [pageState, setPageState] = useState({ key: queryKey, page: 1 })
  const page = pageState.key === queryKey ? pageState.page : 1

  const fetchProblems = useCallback(
    () =>
      problemService.list({
        search: debouncedSearch,
        difficulty: difficulty === 'ALL' ? undefined : difficulty,
        topic: topic === 'all' ? undefined : topic,
        tags: tag === 'all' ? undefined : [tag],
        status: status === 'all' ? undefined : status,
        page,
        pageSize: PAGE_SIZE,
      }),
    [debouncedSearch, difficulty, topic, tag, status, page],
  )
  const { data, loading, error, reload } = useApiQuery(fetchProblems)
  const filtered = Boolean(debouncedSearch.trim()) || difficulty !== 'ALL' || topic !== 'all' || tag !== 'all' || status !== 'all'

  const resetFilters = () => {
    setSearch('')
    setDifficulty('ALL')
    setTopic('all')
    setTag('all')
    setStatus('all')
  }

  return (
    <div className="animate-fade-in">
      <PageHeader
        eyebrow={isStaff ? 'Content · Library' : 'Practice'}
        title="Problems"
        description={
          isStaff ? 'Browse the published problem library.' : 'Practice coding problems and improve your skills.'
        }
      />

      {isStaff && (
        <Alert variant="info" className="mb-4">
          Staff problem management will be available in a future phase. You can browse published problems below.
        </Alert>
      )}

      <Card className="p-4">
        <div className="flex items-center gap-2 font-mono text-[11px] tracking-[0.14em] text-ink-400 uppercase">
          <Filter className="size-3.5" aria-hidden /> Filters
        </div>
        <div className="mt-3 grid gap-3 md:grid-cols-2 xl:grid-cols-[minmax(0,1fr)_auto_12rem_12rem_auto] xl:items-end">
          <SearchInput
            className="md:col-span-2 xl:col-span-1"
            value={search}
            onChange={setSearch}
            label="Search problems"
            placeholder="Search by title or tag..."
            maxLength={100}
          />
          <div>
            <p className="mb-1.5 text-xs font-semibold text-ink-500">Difficulty</p>
            <Tabs<DifficultyFilter> ariaLabel="Difficulty" size="sm" value={difficulty} onChange={setDifficulty} options={DIFFICULTY_OPTIONS} />
          </div>
          <Select label="Topic" value={topic} onChange={setTopic} options={topicOptions} disabled={topics.loading && !topics.data} />
          <Select label="Tag" value={tag} onChange={setTag} options={tagOptions} disabled={tags.loading && !tags.data} />
          {!isStaff && (
            <div>
              <p className="mb-1.5 text-xs font-semibold text-ink-500">Status</p>
              <Tabs<StatusFilter> ariaLabel="Status" size="sm" value={status} onChange={setStatus} options={STATUS_OPTIONS} />
            </div>
          )}
        </div>
      </Card>

      <Card className="mt-6 overflow-hidden">
        {loading && !data ? (
          <TableSkeleton rows={6} />
        ) : error ? (
          <div className="space-y-3 p-4">
            <Alert variant="error">Unable to load problems. {error}</Alert>
            <Button size="sm" variant="secondary" icon={<RefreshCw className="size-4" aria-hidden />} onClick={reload}>
              Try Again
            </Button>
          </div>
        ) : !data || data.items.length === 0 ? (
          <div className="p-4">
            <EmptyState
              icon={<Code2 />}
              title="No problems found."
              description={filtered ? 'Try a different search term or clear the filters.' : 'Published problems will appear here.'}
              actionLabel={filtered ? 'Clear filters' : undefined}
              onAction={filtered ? resetFilters : undefined}
            />
          </div>
        ) : (
          <div className={cn('transition-opacity', loading && 'opacity-60')} aria-busy={loading || undefined}>
            <ProblemList problems={data.items} basePath={basePath} showStatus={!isStaff} caption="Problems" />
          </div>
        )}

        {data && data.total > 0 && (
          <Pagination
            page={page}
            totalPages={data.total_pages}
            total={data.total}
            noun="problem"
            disabled={loading}
            onChange={(next) => setPageState({ key: queryKey, page: next })}
          />
        )}
      </Card>
    </div>
  )
}
