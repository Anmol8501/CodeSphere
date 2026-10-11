import { useCallback, useEffect, useRef, useState, type KeyboardEvent, type PointerEvent, type ReactNode } from 'react'
import { splitStore } from '../../utils/workspaceStorage'

interface SplitPaneProps {
  left: ReactNode
  right: ReactNode
  /** Minimum widths in px so neither panel becomes unusable. */
  minLeft?: number
  minRight?: number
}

const DEFAULT_PERCENT = 42
const KEY_STEP = 3

/**
 * Desktop two-panel layout with a draggable, keyboard-accessible divider
 * (Arrow keys / Home / End). The split is remembered in this browser.
 */
export function SplitPane({ left, right, minLeft = 300, minRight = 440 }: SplitPaneProps) {
  const container = useRef<HTMLDivElement>(null)
  const [percent, setPercent] = useState(() => splitStore.get() ?? DEFAULT_PERCENT)
  const [dragging, setDragging] = useState(false)
  const [width, setWidth] = useState(1200)

  useEffect(() => {
    const element = container.current
    if (!element) return
    const observer = new ResizeObserver(([entry]) => setWidth(entry.contentRect.width))
    observer.observe(element)
    return () => observer.disconnect()
  }, [])

  const clamp = useCallback(
    (value: number) => {
      const min = (minLeft / width) * 100
      const max = 100 - (minRight / width) * 100
      return Math.min(Math.max(value, min), Math.max(min, max))
    },
    [minLeft, minRight, width],
  )

  const commit = (value: number) => {
    const next = clamp(value)
    setPercent(next)
    splitStore.set(Math.round(next * 10) / 10)
  }

  const onPointerMove = (event: PointerEvent<HTMLDivElement>) => {
    if (!dragging || !container.current) return
    const rect = container.current.getBoundingClientRect()
    commit(((event.clientX - rect.left) / rect.width) * 100)
  }

  const onKeyDown = (event: KeyboardEvent<HTMLDivElement>) => {
    const moves: Record<string, number> = { ArrowLeft: -KEY_STEP, ArrowRight: KEY_STEP }
    if (event.key in moves) commit(percent + moves[event.key])
    else if (event.key === 'Home') commit(0)
    else if (event.key === 'End') commit(100)
    else return
    event.preventDefault()
  }

  const shown = clamp(percent)

  return (
    <div ref={container} className="flex h-full min-h-0 w-full" style={dragging ? { cursor: 'col-resize', userSelect: 'none' } : undefined}>
      <div className="min-h-0 min-w-0 overflow-hidden" style={{ width: `${shown}%` }}>
        {left}
      </div>
      <div
        role="separator"
        aria-orientation="vertical"
        aria-label="Resize problem and editor panels"
        aria-valuenow={Math.round(shown)}
        aria-valuemin={0}
        aria-valuemax={100}
        tabIndex={0}
        onKeyDown={onKeyDown}
        onPointerDown={(event) => {
          event.currentTarget.setPointerCapture(event.pointerId)
          setDragging(true)
        }}
        onPointerMove={onPointerMove}
        onPointerUp={() => setDragging(false)}
        onPointerCancel={() => setDragging(false)}
        onDoubleClick={() => commit(DEFAULT_PERCENT)}
        className="group relative z-10 w-1.5 shrink-0 cursor-col-resize bg-ink-200/60 outline-none transition-colors hover:bg-brand-500/40 focus-visible:bg-brand-500/60"
      >
        <span className="absolute inset-y-0 -right-1.5 -left-1.5" aria-hidden />
        <span className="absolute top-1/2 left-1/2 h-8 w-0.5 -translate-x-1/2 -translate-y-1/2 rounded-full bg-ink-400 group-hover:bg-brand-400" aria-hidden />
      </div>
      <div className="min-h-0 min-w-0 flex-1 overflow-hidden">{right}</div>
    </div>
  )
}
