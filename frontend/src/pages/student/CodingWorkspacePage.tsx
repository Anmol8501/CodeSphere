import { ArrowLeft } from 'lucide-react'
import { useCallback } from 'react'
import { Link, useParams } from 'react-router-dom'
import { CodingWorkspace } from '../../components/workspace/CodingWorkspace'
import { EditorSkeleton } from '../../components/workspace/LazyCodeEditor'
import { ErrorState } from '../../components/ui/ErrorState'
import { Skeleton } from '../../components/ui/LoadingState'
import { useApiQuery } from '../../hooks/useApiQuery'
import { useAuth } from '../../hooks/useAuth'
import { problemService } from '../../services/problemService'

function WorkspaceSkeleton() {
  return (
    <div className="flex h-dvh flex-col bg-night" role="status" aria-label="Loading coding workspace">
      <span className="sr-only">Loading coding workspace</span>
      <div className="flex h-14 items-center gap-3 border-b border-ink-200 bg-surface px-4">
        <Skeleton className="size-8 rounded-lg" />
        <Skeleton className="h-4 w-48" />
        <Skeleton className="ml-auto h-8 w-28 rounded-lg" />
      </div>
      <div className="flex min-h-0 flex-1">
        <div className="hidden w-[42%] space-y-3 border-r border-ink-200 bg-card p-5 lg:block">
          <Skeleton className="h-6 w-2/3" />
          <Skeleton className="h-4 w-1/3" />
          <Skeleton className="mt-6 h-4 w-full" />
          <Skeleton className="h-4 w-11/12" />
          <Skeleton className="h-4 w-4/5" />
        </div>
        <div className="flex-1">
          <EditorSkeleton label="Loading problem" />
        </div>
      </div>
    </div>
  )
}

/**
 * /student/problems/:slug/solve. The problem is loaded through the same
 * published-only API as the detail page, so drafts or archived problems are
 * "not found" here too.
 */
export default function CodingWorkspacePage() {
  const { slug = '' } = useParams()
  const { user } = useAuth()
  const fetchProblem = useCallback(() => problemService.get(slug), [slug])
  const { data: problem, loading, error, reload } = useApiQuery(fetchProblem)

  if (loading && !problem) return <WorkspaceSkeleton />
  if (error || !problem || !user) {
    return (
      <div className="min-h-dvh bg-night px-4 py-10">
        <Link
          to="/student/problems"
          className="mx-auto mb-2 flex max-w-lg items-center gap-1.5 text-sm font-semibold text-ink-500 hover:text-brand-400"
        >
          <ArrowLeft className="size-4" aria-hidden /> Back to Problems
        </Link>
        <ErrorState title="Unable to load problem." message={error ?? 'No data received.'} onRetry={reload} />
      </div>
    )
  }

  // Keyed by problem + user: switching either starts a fresh workspace state.
  return <CodingWorkspace key={`${user.id}-${problem.id}`} problem={problem} user={user} />
}
