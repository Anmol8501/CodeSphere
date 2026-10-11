import { AlertTriangle, CheckCircle2, Info, X, XCircle } from 'lucide-react'
import type { ReactNode } from 'react'
import { cn } from '../../utils/format'

type AlertVariant = 'error' | 'success' | 'info' | 'warning'

const STYLES: Record<AlertVariant, { box: string; icon: ReactNode }> = {
  error: {
    box: 'border-danger/30 bg-danger/10 text-ink-900',
    icon: <XCircle className="size-[18px] text-danger" aria-hidden />,
  },
  success: {
    box: 'border-brand-500/30 bg-brand-500/10 text-ink-900',
    icon: <CheckCircle2 className="size-[18px] text-brand-500" aria-hidden />,
  },
  info: {
    box: 'border-info/30 bg-info/10 text-ink-900',
    icon: <Info className="size-[18px] text-info" aria-hidden />,
  },
  warning: {
    box: 'border-warning/30 bg-warning/10 text-ink-900',
    icon: <AlertTriangle className="size-[18px] text-warning" aria-hidden />,
  },
}

interface AlertProps {
  variant?: AlertVariant
  children: ReactNode
  onDismiss?: () => void
  className?: string
}

export function Alert({ variant = 'error', children, onDismiss, className }: AlertProps) {
  const style = STYLES[variant]
  return (
    <div
      role={variant === 'error' ? 'alert' : 'status'}
      className={cn(
        'flex animate-fade-in items-start gap-2.5 rounded-xl border px-3.5 py-3 text-sm',
        style.box,
        className,
      )}
    >
      <span className="mt-px shrink-0">{style.icon}</span>
      <div className="min-w-0 flex-1 leading-relaxed">{children}</div>
      {onDismiss && (
        <button
          type="button"
          onClick={onDismiss}
          className="-m-1 rounded-md p-1 text-ink-500 transition hover:text-ink-950"
          aria-label="Dismiss"
        >
          <X className="size-4" />
        </button>
      )}
    </div>
  )
}
