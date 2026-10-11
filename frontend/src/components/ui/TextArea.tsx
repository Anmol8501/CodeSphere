import { AlertCircle } from 'lucide-react'
import { useId, type ReactNode, type TextareaHTMLAttributes } from 'react'
import { cn } from '../../utils/format'

export interface TextAreaProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  label: string
  error?: string
  hint?: ReactNode
  /** Monospace text (code, test data, constraints). */
  mono?: boolean
  /** Visually hide the label (it stays available to screen readers). */
  hideLabel?: boolean
}

export function TextArea({ label, error, hint, mono, hideLabel, id, className, rows = 4, ...rest }: TextAreaProps) {
  const generatedId = useId()
  const inputId = id ?? generatedId
  const describedBy = error ? `${inputId}-error` : hint ? `${inputId}-hint` : undefined

  return (
    <div className={className}>
      <label htmlFor={inputId} className={cn('mb-1.5 block text-sm font-semibold text-ink-800', hideLabel && 'sr-only')}>
        {label}
      </label>
      <textarea
        id={inputId}
        rows={rows}
        aria-invalid={error ? true : undefined}
        aria-describedby={describedBy}
        spellCheck={mono ? false : undefined}
        className={cn(
          'block w-full resize-y rounded-xl border bg-night px-3.5 py-2.5 text-ink-950 transition',
          'placeholder:text-ink-400 focus:outline-none focus:ring-4 disabled:opacity-60',
          mono ? 'font-mono text-[13px] leading-relaxed' : 'text-[15px]',
          error
            ? 'border-danger/70 focus:border-danger focus:ring-danger/15'
            : 'border-ink-200 hover:border-ink-300 focus:border-brand-500 focus:ring-brand-500/15',
        )}
        {...rest}
      />
      {error ? (
        <p id={`${inputId}-error`} className="mt-1.5 flex items-start gap-1.5 text-[13px] text-danger">
          <AlertCircle className="mt-0.5 size-3.5 shrink-0" aria-hidden />
          {error}
        </p>
      ) : hint ? (
        <p id={`${inputId}-hint`} className="mt-1.5 text-[13px] text-ink-500">
          {hint}
        </p>
      ) : null}
    </div>
  )
}
