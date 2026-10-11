import { cn } from '../../utils/format'

// A decorative, hand-highlighted code snippet. Purely visual.
const LINES: { indent: number; tokens: [string, string][] }[] = [
  { indent: 0, tokens: [['text-ink-500', '# your journey, one commit at a time']] },
  {
    indent: 0,
    tokens: [
      ['text-accent', 'def '],
      ['text-brand-400', 'arena'],
      ['text-ink-800', '(student):'],
    ],
  },
  {
    indent: 1,
    tokens: [
      ['text-accent', 'while '],
      ['text-ink-800', 'student.curious:'],
    ],
  },
  { indent: 2, tokens: [['text-brand-400', 'learn'], ['text-ink-800', '()'], ['text-ink-400', '   # master DSA']] },
  { indent: 2, tokens: [['text-brand-400', 'code'], ['text-ink-800', '()'], ['text-ink-400', '    # solve problems']] },
  { indent: 2, tokens: [['text-brand-400', 'compete'], ['text-ink-800', '()'], ['text-ink-400', ' # climb the ranks']] },
  {
    indent: 1,
    tokens: [
      ['text-accent', 'return '],
      ['text-warning', '"ready for placements"'],
    ],
  },
]

export function CodeWindow({ className }: { className?: string }) {
  return (
    <div
      className={cn(
        'overflow-hidden rounded-2xl border border-brand-500/15 bg-night/90 shadow-2xl shadow-black/60 backdrop-blur',
        className,
      )}
      aria-hidden
    >
      <div className="flex items-center gap-2 border-b border-brand-500/15 px-4 py-3">
        <span className="size-2.5 rounded-full bg-danger/80" />
        <span className="size-2.5 rounded-full bg-warning/80" />
        <span className="size-2.5 rounded-full bg-brand-500/80" />
        <span className="ml-3 font-mono text-xs text-ink-500">arena.py</span>
      </div>
      <pre className="overflow-hidden px-4 py-4 font-mono text-[12.5px] leading-6">
        {LINES.map((line, index) => (
          <div key={index} className="flex">
            <span className="mr-4 w-4 shrink-0 text-right text-ink-400 select-none">{index + 1}</span>
            <span style={{ paddingLeft: `${line.indent * 1.5}rem` }}>
              {line.tokens.map(([color, text], i) => (
                <span key={i} className={color}>
                  {text}
                </span>
              ))}
            </span>
          </div>
        ))}
        <div className="flex">
          <span className="mr-4 w-4 shrink-0 text-right text-ink-400 select-none">{LINES.length + 1}</span>
          <span className="inline-block h-5 w-2 translate-y-0.5 animate-pulse bg-brand-500" />
        </div>
      </pre>
    </div>
  )
}
