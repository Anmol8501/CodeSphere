import type { KeyboardEvent, ReactNode } from 'react'
import { cn } from '../../utils/format'

export interface TabOption<T extends string> {
  value: T
  label: string
  icon?: ReactNode
}

interface TabsProps<T extends string> {
  options: TabOption<T>[]
  value: T
  onChange: (value: T) => void
  ariaLabel: string
  size?: 'sm' | 'md'
  className?: string
}

/** Segmented control (used for filters). Arrow keys move between options. */
export function Tabs<T extends string>({ options, value, onChange, ariaLabel, size = 'md', className }: TabsProps<T>) {
  const onKeyDown = (event: KeyboardEvent<HTMLDivElement>) => {
    if (event.key !== 'ArrowRight' && event.key !== 'ArrowLeft') return
    event.preventDefault()
    const index = options.findIndex((o) => o.value === value)
    const next = (index + (event.key === 'ArrowRight' ? 1 : -1) + options.length) % options.length
    onChange(options[next].value)
    const buttons = event.currentTarget.querySelectorAll<HTMLButtonElement>('[role="tab"]')
    buttons[next]?.focus()
  }

  return (
    <div
      role="tablist"
      aria-label={ariaLabel}
      onKeyDown={onKeyDown}
      className={cn('inline-flex max-w-full gap-1 overflow-x-auto rounded-xl bg-night p-1 ring-1 ring-ink-200', className)}
    >
      {options.map((option) => {
        const active = option.value === value
        return (
          <button
            key={option.value}
            type="button"
            role="tab"
            aria-selected={active}
            tabIndex={active ? 0 : -1}
            onClick={() => onChange(option.value)}
            className={cn(
              'inline-flex shrink-0 items-center gap-1.5 rounded-lg font-semibold whitespace-nowrap transition',
              size === 'sm' ? 'h-7 px-2.5 text-xs' : 'h-8 px-3.5 text-sm',
              active
                ? 'bg-brand-500/10 text-brand-500 ring-1 ring-brand-500/40'
                : 'text-ink-500 hover:text-ink-900',
            )}
          >
            {option.icon}
            {option.label}
          </button>
        )
      })}
    </div>
  )
}
