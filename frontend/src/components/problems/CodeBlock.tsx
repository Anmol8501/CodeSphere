import { cn } from '../../utils/format'

/** Labelled monospace block for example / test-case input and output. */
export function CodeBlock({ label, value, className }: { label: string; value: string; className?: string }) {
  return (
    <div className={cn('min-w-0', className)}>
      <p className="mb-1 font-mono text-[10px] tracking-[0.2em] text-ink-400 uppercase">{label}</p>
      <pre className="max-h-48 overflow-auto rounded-lg bg-night px-3 py-2 font-mono text-[13px] whitespace-pre-wrap text-ink-900 ring-1 ring-ink-200">
        {value || ' '}
      </pre>
    </div>
  )
}
