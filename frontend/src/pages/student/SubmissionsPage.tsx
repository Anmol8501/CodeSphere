import { Award, History, X } from 'lucide-react'
import { useCallback, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { VerdictBadge } from '../../components/submissions/VerdictBadge'
import { Alert } from '../../components/ui/Alert'
import { Card } from '../../components/ui/Card'
import { EmptyState } from '../../components/ui/EmptyState'
import { TableSkeleton } from '../../components/ui/LoadingState'
import { PageHeader } from '../../components/ui/PageHeader'
import { Pagination } from '../../components/ui/Pagination'
import { SearchInput } from '../../components/ui/SearchInput'
import { Select } from '../../components/ui/Select'
import { Tabs } from '../../components/ui/Tabs'
import { formatMemory, formatRuntime, VERDICTS } from '../../components/workspace/verdicts'
import { LANGUAGE_CONFIG } from '../../config/languages'
import { useApiQuery } from '../../hooks/useApiQuery'
import { useAppTimezone } from '../../hooks/useAppTimezone'
import { useDebouncedValue } from '../../hooks/useDebouncedValue'
import { submissionService } from '../../services/submissionService'
import type { SubmissionPeriod, SubmissionStatus, SupportedLanguage } from '../../types/workspace'
import { formatDateTime, timeAgo } from '../../utils/dates'
import { cn } from '../../utils/format'

const PAGE_SIZE = 20
const STATUS_FILTERS: SubmissionStatus[] = [
  'ACCEPTED', 'WRONG_ANSWER', 'COMPILE_ERROR', 'RUNTIME_ERROR', 'TIME_LIMIT_EXCEEDED',
  'MEMORY_LIMIT_EXCEEDED', 'OUTPUT_LIMIT_EXCEEDED', 'SYSTEM_ERROR', 'EXECUTION_TIMEOUT',
]
const PERIODS: { value: SubmissionPeriod; label: string }[] = [
  { value: 'all', label: 'All time' },
  { value: 'today', label: 'Today' },
  { value: '7d', label: '7 days' },
  { value: '30d', label: '30 days' },
]

/** The student's own submissions (the API never returns anyone else's). */
export default function SubmissionsPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const problem = searchParams.get('problem') ?? undefined
  const [search, setSearch] = useState('')
  const debouncedSearch = useDebouncedValue(search)
  const [language, setLanguage] = useState<'ALL' | SupportedLanguage>('ALL')
  const [status, setStatus] = useState<'ALL' | SubmissionStatus>('ALL')
  const [period, setPeriod] = useState<SubmissionPeriod>('all')
  const queryKey = `${problem}|${debouncedSearch.trim()}|${language}|${status}|${period}`
  const [pageState, setPageState] = useState({ key: queryKey, page: 1 })
  const page = pageState.key === queryKey ? pageState.page : 1
  const timezone = useAppTimezone()

  const fetchSubmissions = useCallback(
    () =>
      submissionService.list({
        problem,
        search: debouncedSearch,
        language: language === 'ALL' ? undefined : language,
        status: status === 'ALL' ? undefined : status,
        period,
        page,
        limit: PAGE_SIZE,
      }),
    [problem, debouncedSearch, language, status, period, page],
  )
  const { data, loading, error } = useApiQuery(fetchSubmissions)
  const filtered = Boolean(problem) || Boolean(debouncedSearch.trim()) || language !== 'ALL' || status !== 'ALL' || period !== 'all'
  const when = (iso: string) => (timezone ? formatDateTime(iso, timezone) : '')

  return (
    <div className="animate-fade-in">
      <PageHeader eyebrow="Practice · History" title="Submission History" description="Every solution you have submitted, with its verdict, runtime and memory." />

      <Card className="overflow-hidden">
        <div className="space-y-3 border-b border-ink-200 p-4">
          <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-[minmax(0,1fr)_11rem_14rem]">
            <SearchInput
              className="md:col-span-2 xl:col-span-1"
              value={search}
              onChange={setSearch}
              label="Search submissions"
              placeholder="Search submissions by problem..."
              maxLength={100}
            />
            <Select<'ALL' | SupportedLanguage>
              label="Language"
              value={language}
              onChange={setLanguage}
              options={[
                { value: 'ALL', label: 'All languages' },
                ...(Object.keys(LANGUAGE_CONFIG) as SupportedLanguage[]).map((l) => ({ value: l, label: LANGUAGE_CONFIG[l].label })),
              ]}
            />
            <Select<'ALL' | SubmissionStatus>
              label="Verdict"
              value={status}
              onChange={setStatus}
              options={[{ value: 'ALL', label: 'All verdicts' }, ...STATUS_FILTERS.map((s) => ({ value: s, label: VERDICTS[s].label }))]}
            />
          </div>
          <div className="flex flex-wrap items-end gap-3">
            <div className="max-w-full overflow-x-auto">
              <p className="mb-1.5 text-xs font-semibold text-ink-500">Date</p>
              <Tabs<SubmissionPeriod> ariaLabel="Date range" size="sm" value={period} onChange={setPeriod} options={PERIODS} />
            </div>
            {problem && (
              <div className="flex items-center gap-2 rounded-lg bg-night px-2.5 py-1.5 text-xs ring-1 ring-ink-200">
                <span className="text-ink-500">Problem:</span>
                <span className="font-mono text-ink-900">{problem}</span>
                <button
                  type="button"
                  aria-label="Clear problem filter"
                  onClick={() => setSearchParams({})}
                  className="rounded p-0.5 text-ink-400 hover:text-ink-950"
                >
                  <X className="size-3.5" />
                </button>
              </div>
            )}
          </div>
        </div>

        {loading && !data ? (
          <TableSkeleton />
        ) : error ? (
          <div className="p-4">
            <Alert variant="error">Unable to load submissions. {error}</Alert>
          </div>
        ) : !data || data.items.length === 0 ? (
          <div className="p-4">
            <EmptyState
              icon={<History />}
              title={filtered ? 'No submissions match these filters.' : 'No submissions yet.'}
              description={filtered ? undefined : 'Solve a problem and press Submit to see it here.'}
              actionLabel={filtered ? undefined : 'Browse Problems'}
              actionTo={filtered ? undefined : '/student/problems'}
            />
          </div>
        ) : (
          <div className={cn('transition-opacity', loading && 'opacity-60')} aria-busy={loading || undefined}>
            <div className="hidden overflow-x-auto md:block">
              <table className="w-full text-left text-sm">
                <caption className="sr-only">Your submissions</caption>
                <thead className="border-b border-ink-200 bg-night/60 font-mono text-[11px] tracking-[0.14em] text-ink-400 uppercase">
                  <tr>
                    <th scope="col" className="px-4 py-3 font-semibold">Problem</th>
                    <th scope="col" className="px-4 py-3 font-semibold">Language</th>
                    <th scope="col" className="px-4 py-3 font-semibold">Verdict</th>
                    <th scope="col" className="px-4 py-3 font-semibold">Tests</th>
                    <th scope="col" className="px-4 py-3 font-semibold">Runtime</th>
                    <th scope="col" className="px-4 py-3 font-semibold">Memory</th>
                    <th scope="col" className="px-4 py-3 font-semibold">Submitted</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-ink-200">
                  {data.items.map((s) => (
                    <tr key={s.id} className="transition hover:bg-ink-100/50">
                      <td className="px-4 py-3">
                        <Link to={`/student/submissions/${s.id}`} className="font-semibold text-ink-950 hover:text-brand-400 hover:underline">
                          {s.problem.title}
                        </Link>
                        {s.is_first_accepted && (
                          <span className="ml-2 inline-flex items-center gap-1 font-mono text-[10px] text-brand-400" title="First accepted submission">
                            <Award className="size-3" aria-hidden /> first solve
                          </span>
                        )}
                      </td>
                      <td className="px-4 py-3 font-mono text-xs text-ink-500">{LANGUAGE_CONFIG[s.language].label}</td>
                      <td className="px-4 py-3"><VerdictBadge verdict={s.status} /></td>
                      <td className="px-4 py-3 font-mono text-xs text-ink-500 tabular-nums">{s.passed_tests} / {s.total_tests}</td>
                      <td className="px-4 py-3 font-mono text-xs text-ink-500 tabular-nums">{formatRuntime(s.runtime_ms)}</td>
                      <td className="px-4 py-3 font-mono text-xs text-ink-500 tabular-nums">{formatMemory(s.memory_kb)}</td>
                      <td className="px-4 py-3 font-mono text-xs whitespace-nowrap text-ink-400" title={when(s.submitted_at)}>
                        {timeAgo(s.submitted_at)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <ul className="divide-y divide-ink-200 md:hidden" aria-label="Your submissions">
              {data.items.map((s) => (
                <li key={s.id}>
                  <Link to={`/student/submissions/${s.id}`} className="block space-y-2 p-4 transition hover:bg-ink-100/50">
                    <span className="block font-semibold break-words text-ink-950">{s.problem.title}</span>
                    <span className="flex flex-wrap items-center gap-2">
                      <VerdictBadge verdict={s.status} />
                      <span className="font-mono text-xs text-ink-500">{LANGUAGE_CONFIG[s.language].label}</span>
                      <span className="font-mono text-xs text-ink-500">{s.passed_tests}/{s.total_tests}</span>
                    </span>
                    <span className="block font-mono text-[11px] text-ink-400">
                      {formatRuntime(s.runtime_ms)} · {formatMemory(s.memory_kb)} · {timeAgo(s.submitted_at)}
                    </span>
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        )}

        {data && data.total > 0 && (
          <Pagination page={page} totalPages={data.total_pages} total={data.total} noun="submission" disabled={loading}
            onChange={(next) => setPageState({ key: queryKey, page: next })} />
        )}
      </Card>
    </div>
  )
}
