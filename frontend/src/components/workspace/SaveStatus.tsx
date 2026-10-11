import { AlertTriangle, Check, CloudOff, GitMerge, Loader2, RefreshCw } from 'lucide-react'
import type { ReactNode } from 'react'
import type { SaveState } from '../../types/workspace'
import { cn } from '../../utils/format'

const CONFIG: Record<SaveState, { label: string; className: string; icon: ReactNode }> = {
  initializing: { label: 'Initializing...', className: 'text-ink-400', icon: <Loader2 className="size-3.5 animate-spin" aria-hidden /> },
  idle: { label: 'Starter code', className: 'text-ink-400', icon: <span className="size-1.5 rounded-full bg-ink-400" aria-hidden /> },
  saved: { label: 'Saved', className: 'text-brand-400', icon: <Check className="size-3.5" aria-hidden /> },
  unsaved: { label: 'Unsaved changes', className: 'text-ink-500', icon: <span className="size-1.5 rounded-full bg-warning" aria-hidden /> },
  saving: { label: 'Saving...', className: 'text-ink-500', icon: <Loader2 className="size-3.5 animate-spin" aria-hidden /> },
  error: { label: 'Save failed', className: 'text-danger', icon: <AlertTriangle className="size-3.5" aria-hidden /> },
  offline: { label: 'Offline: kept in this browser', className: 'text-warning', icon: <CloudOff className="size-3.5" aria-hidden /> },
  conflict: { label: 'Changed in another tab', className: 'text-warning', icon: <GitMerge className="size-3.5" aria-hidden /> },
}

/** "Saved" is only shown after the server confirms the save. */
export function SaveStatus({ state, onRetry, compact }: { state: SaveState; onRetry?: () => void; compact?: boolean }) {
  const { label, className, icon } = CONFIG[state]
  const canRetry = (state === 'error' || state === 'offline') && onRetry
  return (
    <div className="flex items-center gap-1.5">
      <span
        role="status"
        aria-live="polite"
        aria-label={`Draft status: ${label}`}
        data-save-state={state}
        className={cn('inline-flex items-center gap-1.5 font-mono text-[11px] font-semibold whitespace-nowrap', className)}
      >
        {icon}
        <span className={cn(compact && 'sr-only')}>{label}</span>
      </span>
      {canRetry && (
        <button
          type="button"
          onClick={onRetry}
          className="inline-flex items-center gap-1 rounded-md px-1.5 py-0.5 text-[11px] font-semibold text-ink-700 ring-1 ring-ink-200 transition hover:text-ink-950 hover:ring-brand-500/40"
        >
          <RefreshCw className="size-3" aria-hidden /> Retry
        </button>
      )}
    </div>
  )
}
