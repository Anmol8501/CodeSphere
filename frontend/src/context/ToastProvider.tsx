import { AlertTriangle, CheckCircle2, Info, X, XCircle } from 'lucide-react'
import { useCallback, useMemo, useRef, useState, type ReactNode } from 'react'
import { createPortal } from 'react-dom'
import { useOverlayRoot } from '../hooks/useFullscreenElement'
import { cn } from '../utils/format'
import { ToastContext, type ToastOptions, type ToastVariant } from './toastContextValue'

interface ToastItem {
  id: number
  message: string
  variant: ToastVariant
}

const STYLES: Record<ToastVariant, { box: string; icon: ReactNode }> = {
  success: { box: 'border-brand-500/30', icon: <CheckCircle2 className="size-4 text-brand-500" aria-hidden /> },
  error: { box: 'border-danger/40', icon: <XCircle className="size-4 text-danger" aria-hidden /> },
  info: { box: 'border-info/30', icon: <Info className="size-4 text-info" aria-hidden /> },
  warning: { box: 'border-warning/40', icon: <AlertTriangle className="size-4 text-warning" aria-hidden /> },
}

const MAX_TOASTS = 3

/** The app's single toast system. Use `useToast()` to show a message. */
export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<ToastItem[]>([])
  const nextId = useRef(0)
  const overlayRoot = useOverlayRoot()

  const dismiss = useCallback((id: number) => setToasts((list) => list.filter((t) => t.id !== id)), [])

  const toast = useCallback(
    (message: string, { variant = 'info', duration = 3500 }: ToastOptions = {}) => {
      const id = ++nextId.current
      // The same message twice in a row replaces the old one instead of stacking.
      setToasts((list) => [...list.filter((t) => t.message !== message), { id, message, variant }].slice(-MAX_TOASTS))
      if (duration > 0) window.setTimeout(() => dismiss(id), duration)
    },
    [dismiss],
  )

  const value = useMemo(() => ({ toast }), [toast])

  return (
    <ToastContext.Provider value={value}>
      {children}
      {createPortal(
        <div
          aria-live="polite"
          aria-label="Notifications"
          className="pointer-events-none fixed right-4 bottom-4 left-4 z-[60] flex flex-col items-end gap-2 sm:left-auto"
        >
          {toasts.map((t) => (
            <div
              key={t.id}
              role={t.variant === 'error' ? 'alert' : 'status'}
              className={cn(
                'pointer-events-auto flex w-full max-w-sm animate-fade-in items-start gap-2.5 rounded-xl border bg-surface/95 px-3.5 py-3 text-sm text-ink-900 shadow-lift backdrop-blur',
                STYLES[t.variant].box,
              )}
            >
              <span className="mt-0.5 shrink-0">{STYLES[t.variant].icon}</span>
              <p className="min-w-0 flex-1">{t.message}</p>
              <button
                type="button"
                onClick={() => dismiss(t.id)}
                className="-m-1 rounded-md p-1 text-ink-400 transition hover:text-ink-950"
                aria-label="Dismiss notification"
              >
                <X className="size-4" />
              </button>
            </div>
          ))}
        </div>,
        overlayRoot,
      )}
    </ToastContext.Provider>
  )
}
