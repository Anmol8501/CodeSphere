import { cn } from '../../../utils/format'

export interface TerminalBlock {
  label: string
  text: string | null
  tone?: 'default' | 'error'
}

/** Terminal-style read-only output (rendered as text, never as HTML). */
export function OutputTerminal({ blocks, emptyText = 'No output.' }: { blocks: TerminalBlock[]; emptyText?: string }) {
  const visible = blocks.filter((b) => b.text !== null)
  if (visible.length === 0) return <p className="font-mono text-xs text-ink-400">{emptyText}</p>
  return (
    <div className="space-y-3">
      {visible.map((block) => (
        <div key={block.label}>
          <p className="mb-1 font-mono text-[10px] tracking-[0.2em] text-ink-400 uppercase">{block.label}</p>
          <pre
            className={cn(
              'max-h-56 overflow-auto rounded-lg bg-[#050805] px-3 py-2 font-mono text-[12.5px] leading-relaxed whitespace-pre-wrap ring-1',
              block.tone === 'error' ? 'text-danger ring-danger/25' : 'text-ink-900 ring-ink-200',
            )}
          >
            {block.text || '(empty)'}
          </pre>
        </div>
      ))}
    </div>
  )
}
