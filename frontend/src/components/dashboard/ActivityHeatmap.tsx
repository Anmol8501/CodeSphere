import { useEffect, useMemo, useRef, useState } from 'react'
import type { Heatmap } from '../../types/progress'
import { formatDayKey, weekdayOf } from '../../utils/dates'
import { cn } from '../../utils/format'

// Sequential single-hue ramp (validated: monotone lightness, light end >= 2:1 vs the card surface).
const LEVEL_CLASS = [
  'bg-ink-100 ring-1 ring-inset ring-ink-200',
  'bg-[#286520]',
  'bg-[#168a35]',
  'bg-[#20c957]',
  'bg-[#39ff14]',
]
const LEVEL_LABELS = ['0', '1', '2-3', '4-6', '7+']

function level(count: number): number {
  if (count <= 0) return 0
  if (count === 1) return 1
  if (count <= 3) return 2
  if (count <= 6) return 3
  return 4
}

const CELL = 12
const GAP = 3
const WEEKDAY_LABELS = ['', 'Mon', '', 'Wed', '', 'Fri', '']

interface Tip {
  date: string
  count: number
  x: number
  y: number
}

/**
 * GitHub-style contribution grid built only from the server's per-day counts
 * (calendar days in the app timezone). Columns are weeks, rows are weekdays.
 */
export function ActivityHeatmap({ heatmap, unit = 'submission' }: { heatmap: Heatmap; unit?: string }) {
  const scroller = useRef<HTMLDivElement>(null)
  const [tip, setTip] = useState<Tip | null>(null)

  const { columns, monthLabels } = useMemo(() => {
    const pad = weekdayOf(heatmap.start_date) // 0 = Sunday
    const cells: (typeof heatmap.days[number] | null)[] = [...Array(pad).fill(null), ...heatmap.days]
    const cols: (typeof cells)[] = []
    for (let i = 0; i < cells.length; i += 7) cols.push(cells.slice(i, i + 7))
    const labels: { index: number; text: string }[] = []
    let lastMonth = ''
    cols.forEach((col, index) => {
      const first = col.find((c) => c !== null)
      if (!first) return
      const month = first.date.slice(0, 7)
      if (month !== lastMonth) {
        // Skip a label squeezed into the very first partial column.
        if (!(index === 0 && col.filter(Boolean).length < 4)) labels.push({ index, text: formatDayKey(first.date, { short: true }).split(' ')[0] })
        lastMonth = month
      }
    })
    return { columns: cols, monthLabels: labels }
  }, [heatmap])

  // Show the most recent weeks first on narrow screens.
  useEffect(() => {
    const el = scroller.current
    if (el) el.scrollLeft = el.scrollWidth
  }, [columns.length])

  const width = columns.length * (CELL + GAP)
  const activeDays = heatmap.days.filter((d) => d.submission_count > 0)
  const plural = (n: number) => `${n} ${unit}${n === 1 ? '' : 's'}`

  return (
    <div>
      <div className="flex gap-2">
        <div className="shrink-0 pt-[18px]" aria-hidden>
          {WEEKDAY_LABELS.map((label, i) => (
            <div key={i} className="font-mono text-[9px] leading-none text-ink-400" style={{ height: CELL, marginBottom: GAP }}>
              {label}
            </div>
          ))}
        </div>
        <div ref={scroller} className="relative min-w-0 flex-1 overflow-x-auto pb-1" onPointerLeave={() => setTip(null)}>
          <div className="relative" style={{ width }}>
            <div className="relative h-[14px] font-mono text-[9px] text-ink-400" aria-hidden>
              {monthLabels.map((m) => (
                <span key={m.index} className="absolute top-0" style={{ left: m.index * (CELL + GAP) }}>
                  {m.text}
                </span>
              ))}
            </div>
            <div
              role="img"
              aria-label={`Coding activity from ${formatDayKey(heatmap.start_date)} to ${formatDayKey(heatmap.end_date)}: ${plural(heatmap.total_submissions)} on ${heatmap.active_days} active day${heatmap.active_days === 1 ? '' : 's'}`}
              className="mt-1 flex"
              style={{ gap: GAP }}
            >
              {columns.map((col, ci) => (
                <div key={ci} className="flex flex-col" style={{ gap: GAP }}>
                  {col.map((cell, ri) =>
                    cell ? (
                      <span
                        key={cell.date}
                        data-date={cell.date}
                        data-count={cell.submission_count}
                        onPointerEnter={() => setTip({ date: cell.date, count: cell.submission_count, x: ci * (CELL + GAP), y: ri * (CELL + GAP) })}
                        className={cn('block rounded-[3px] transition hover:brightness-125', LEVEL_CLASS[level(cell.submission_count)])}
                        style={{ width: CELL, height: CELL }}
                      />
                    ) : (
                      <span key={`pad-${ri}`} style={{ width: CELL, height: CELL }} aria-hidden />
                    ),
                  )}
                </div>
              ))}
            </div>
            {tip && (
              <div
                role="tooltip"
                className="pointer-events-none absolute z-10 -translate-x-1/2 rounded-md bg-ink-950 px-2 py-1 text-[11px] whitespace-nowrap text-night shadow-lg"
                style={{ left: Math.min(Math.max(tip.x + CELL / 2, 70), width - 70), top: tip.y - 14 }}
              >
                <strong className="font-bold">{plural(tip.count)}</strong> · {formatDayKey(tip.date, { weekday: true })}
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="mt-3 flex flex-wrap items-center justify-between gap-2">
        <p className="text-xs text-ink-500">
          {plural(heatmap.total_submissions)} on {heatmap.active_days} active day{heatmap.active_days === 1 ? '' : 's'}
        </p>
        <div className="flex items-center gap-1.5 font-mono text-[10px] tracking-wider text-ink-400 uppercase" aria-hidden>
          <span>Less</span>
          {LEVEL_CLASS.map((cls, i) => (
            <span key={i} className={cn('size-2.5 rounded-[2px]', cls)} title={`${LEVEL_LABELS[i]} per day`} />
          ))}
          <span>More</span>
        </div>
      </div>

      {/* Text equivalent of the chart for screen readers. */}
      <table className="sr-only">
        <caption>Days with {unit}s</caption>
        <thead>
          <tr>
            <th scope="col">Date</th>
            <th scope="col">{unit}s</th>
          </tr>
        </thead>
        <tbody>
          {activeDays.map((d) => (
            <tr key={d.date}>
              <td>{formatDayKey(d.date)}</td>
              <td>{d.submission_count}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
