import { RefreshCw } from 'lucide-react'
import type { ReactNode } from 'react'
import { Button } from '../ui/Button'
import { Skeleton } from '../ui/LoadingState'

interface SectionBodyProps<T> {
  query: { data: T | null; loading: boolean; error: string | null; reload: () => void }
  children: (data: T) => ReactNode
  /** Skeleton rows while the first load is in flight. */
  rows?: number
  errorText?: string
}

/**
 * Loading / error / content for ONE dashboard section, so a failing request
 * never breaks the rest of the page.
 */
export function SectionBody<T>({ query, children, rows = 3, errorText = 'Unable to load statistics.' }: SectionBodyProps<T>) {
  if (query.loading && !query.data) {
    return (
      <div className="space-y-3" role="status" aria-label="Loading">
        {Array.from({ length: rows }, (_, i) => (
          <Skeleton key={i} className="h-5 w-full" />
        ))}
      </div>
    )
  }
  if (query.error || !query.data) {
    return (
      <div className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-danger/25 bg-danger/[0.05] px-3 py-2.5" role="alert">
        <p className="text-sm text-ink-700">{errorText}</p>
        <Button size="sm" variant="ghost" icon={<RefreshCw className="size-3.5" aria-hidden />} onClick={query.reload}>
          Try again
        </Button>
      </div>
    )
  }
  return <>{children(query.data)}</>
}
