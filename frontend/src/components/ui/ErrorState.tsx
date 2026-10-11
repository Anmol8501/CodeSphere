import { AlertOctagon, RefreshCw } from 'lucide-react'
import { Button } from './Button'
import { Card } from './Card'

interface ErrorStateProps {
  title?: string
  /** A safe, user-facing message (never a stack trace). */
  message: string
  onRetry?: () => void
}

export function ErrorState({ title = 'Unable to load this page.', message, onRetry }: ErrorStateProps) {
  return (
    <Card className="mx-auto mt-10 max-w-lg p-8 text-center" aria-live="polite">
      <span className="mx-auto flex size-12 items-center justify-center rounded-xl bg-danger/10 text-danger ring-1 ring-danger/25">
        <AlertOctagon className="size-6" aria-hidden />
      </span>
      <p className="mt-4 font-mono text-[11px] tracking-[0.18em] text-danger uppercase">Error</p>
      <h2 className="mt-1 text-lg font-bold text-ink-950">{title}</h2>
      <p className="mt-1.5 text-sm text-ink-500">{message}</p>
      {onRetry && (
        <Button variant="secondary" className="mt-5" icon={<RefreshCw className="size-4" />} onClick={onRetry}>
          Try Again
        </Button>
      )}
    </Card>
  )
}
