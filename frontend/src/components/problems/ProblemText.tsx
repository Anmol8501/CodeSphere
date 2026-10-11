import { Fragment, type ReactNode } from 'react'
import { cn } from '../../utils/format'

/**
 * Renders problem text stored as lightweight Markdown: paragraphs, "- " bullet
 * lists, `inline code` and **bold**. Everything is rendered as React text
 * nodes (never as HTML), so stored content cannot inject markup.
 */
function renderInline(text: string): ReactNode[] {
  return text.split(/(`[^`]+`|\*\*[^*]+\*\*)/g).map((part, i) => {
    if (part.startsWith('`') && part.endsWith('`') && part.length > 2) {
      return (
        <code key={i} className="rounded bg-night px-1 py-0.5 font-mono text-[0.85em] text-brand-300 ring-1 ring-ink-200">
          {part.slice(1, -1)}
        </code>
      )
    }
    if (part.startsWith('**') && part.endsWith('**') && part.length > 4) {
      return (
        <strong key={i} className="font-semibold text-ink-950">
          {part.slice(2, -2)}
        </strong>
      )
    }
    return <Fragment key={i}>{part}</Fragment>
  })
}

export function ProblemText({ text, className }: { text: string; className?: string }) {
  const blocks = text.split(/\n{2,}/).filter((block) => block.trim())
  return (
    <div className={cn('space-y-3 text-[15px] leading-relaxed text-ink-700', className)}>
      {blocks.map((block, i) => {
        const lines = block.split('\n')
        if (lines.every((line) => line.trimStart().startsWith('- '))) {
          return (
            <ul key={i} className="list-disc space-y-1 pl-5 marker:text-brand-500">
              {lines.map((line, j) => (
                <li key={j}>{renderInline(line.trimStart().slice(2))}</li>
              ))}
            </ul>
          )
        }
        return (
          <p key={i}>
            {lines.map((line, j) => (
              <Fragment key={j}>
                {j > 0 && <br />}
                {renderInline(line)}
              </Fragment>
            ))}
          </p>
        )
      })}
    </div>
  )
}
