import { useEffect, useId, useRef, useState, type ReactNode } from 'react'
import { cn } from '../../utils/format'

interface DropdownProps {
  /** Renders the trigger button. Spread `props` onto your <button>. */
  trigger: (props: {
    onClick: () => void
    'aria-expanded': boolean
    'aria-haspopup': 'menu' | 'dialog'
    'aria-controls': string
  }) => ReactNode
  /** Panel contents. Call `close()` after an item is chosen. */
  children: (close: () => void) => ReactNode
  align?: 'left' | 'right'
  widthClass?: string
  role?: 'menu' | 'dialog'
  label?: string
}

/** Accessible dropdown: closes on outside click, Escape, or item selection. */
export function Dropdown({
  trigger,
  children,
  align = 'right',
  widthClass = 'w-64',
  role = 'menu',
  label,
}: DropdownProps) {
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)
  const panelId = useId()

  useEffect(() => {
    if (!open) return
    const onClick = (event: MouseEvent) => {
      if (ref.current && !ref.current.contains(event.target as Node)) setOpen(false)
    }
    const onKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') setOpen(false)
    }
    document.addEventListener('mousedown', onClick)
    document.addEventListener('keydown', onKey)
    return () => {
      document.removeEventListener('mousedown', onClick)
      document.removeEventListener('keydown', onKey)
    }
  }, [open])

  const close = () => setOpen(false)

  return (
    <div className="relative" ref={ref}>
      {trigger({
        onClick: () => setOpen((value) => !value),
        'aria-expanded': open,
        'aria-haspopup': role,
        'aria-controls': panelId,
      })}
      {open && (
        <div
          id={panelId}
          role={role}
          aria-label={label}
          className={cn(
            'absolute z-40 mt-2 max-w-[calc(100vw-2rem)] animate-fade-in overflow-hidden rounded-2xl border border-ink-200 bg-surface shadow-lift',
            align === 'right' ? 'right-0' : 'left-0',
            widthClass,
          )}
        >
          {children(close)}
        </div>
      )}
    </div>
  )
}
