import { ChevronLeft, ChevronRight } from 'lucide-react'
import { Button } from './Button'

interface PaginationProps {
  page: number
  totalPages: number
  total: number
  /** Singular noun for the item count, e.g. "problem". */
  noun: string
  onChange: (page: number) => void
  disabled?: boolean
}

export function Pagination({ page, totalPages, total, noun, onChange, disabled }: PaginationProps) {
  const pages = Math.max(1, totalPages)
  return (
    <nav
      aria-label="Pagination"
      className="flex flex-wrap items-center justify-between gap-3 border-t border-ink-200 px-4 py-3 text-sm text-ink-500"
    >
      <p className="font-mono text-xs">
        {total} {noun}
        {total === 1 ? '' : 's'} · Page {page} of {pages}
      </p>
      <div className="flex gap-2">
        <Button
          size="sm"
          variant="secondary"
          icon={<ChevronLeft className="size-4" aria-hidden />}
          disabled={page <= 1 || disabled}
          onClick={() => onChange(page - 1)}
        >
          Prev
        </Button>
        <Button size="sm" variant="secondary" disabled={page >= pages || disabled} onClick={() => onChange(page + 1)}>
          Next <ChevronRight className="size-4" aria-hidden />
        </Button>
      </div>
    </nav>
  )
}
