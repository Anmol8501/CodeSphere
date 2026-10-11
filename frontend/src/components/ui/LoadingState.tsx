import { cn } from '../../utils/format'
import { Card } from './Card'
import { Spinner } from './Spinner'

/** A single shimmering placeholder block. */
export function Skeleton({ className }: { className?: string }) {
  return <div className={cn('animate-shimmer rounded-md bg-ink-200', className)} aria-hidden />
}

/** Spinner + message, used for small areas or route transitions. */
export function PageLoader({ message = 'Loading...' }: { message?: string }) {
  return (
    <div className="flex min-h-[40vh] flex-col items-center justify-center gap-3 text-ink-500" role="status">
      <Spinner className="size-6" />
      <p className="font-mono text-xs tracking-wider uppercase">{message}</p>
    </div>
  )
}

function StatSkeleton() {
  return (
    <Card className="p-5">
      <div className="flex items-start justify-between">
        <Skeleton className="h-3 w-24" />
        <Skeleton className="size-8 rounded-lg" />
      </div>
      <Skeleton className="mt-4 h-7 w-16" />
    </Card>
  )
}

function SectionSkeleton({ className, rows = 3 }: { className?: string; rows?: number }) {
  return (
    <Card className={cn('p-5', className)}>
      <Skeleton className="h-3 w-32" />
      <div className="mt-5 space-y-3">
        {Array.from({ length: rows }, (_, i) => (
          <Skeleton key={i} className={cn('h-4', i % 2 ? 'w-3/4' : 'w-full')} />
        ))}
      </div>
    </Card>
  )
}

/** Dashboard-shaped skeleton: header, four stat cards, two content rows. */
export function DashboardSkeleton({ message = 'Loading dashboard...' }: { message?: string }) {
  return (
    <div role="status" aria-label={message}>
      <span className="sr-only">{message}</span>
      <Card className="mb-6 p-7">
        <Skeleton className="h-3 w-40" />
        <Skeleton className="mt-4 h-8 w-72 max-w-full" />
        <Skeleton className="mt-3 h-4 w-56 max-w-full" />
      </Card>
      <div className="grid grid-cols-2 gap-4 xl:grid-cols-4">
        {Array.from({ length: 4 }, (_, i) => (
          <StatSkeleton key={i} />
        ))}
      </div>
      <div className="mt-6 grid gap-6 lg:grid-cols-3">
        <SectionSkeleton className="lg:col-span-2" rows={4} />
        <SectionSkeleton rows={4} />
      </div>
    </div>
  )
}

/** Table-shaped skeleton for lists. */
export function TableSkeleton({ rows = 5 }: { rows?: number }) {
  return (
    <div className="space-y-3 p-4" role="status" aria-label="Loading">
      {Array.from({ length: rows }, (_, i) => (
        <div key={i} className="flex items-center gap-3">
          <Skeleton className="size-8 shrink-0 rounded-full" />
          <Skeleton className="h-4 flex-1" />
          <Skeleton className="hidden h-4 w-24 sm:block" />
          <Skeleton className="h-7 w-20 rounded-lg" />
        </div>
      ))}
    </div>
  )
}

/** Generic page skeleton used while lazy-loaded pages download. */
export function PageSkeleton() {
  return (
    <div role="status" aria-label="Loading page">
      <Skeleton className="h-3 w-28" />
      <Skeleton className="mt-3 h-8 w-64 max-w-full" />
      <Skeleton className="mt-3 h-4 w-80 max-w-full" />
      <SectionSkeleton className="mt-8" rows={5} />
    </div>
  )
}
