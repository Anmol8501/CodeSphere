// Date helpers for server timestamps. Calendar days are always computed in the
// server's application timezone (see useAppTimezone), never the browser's.

/** "YYYY-MM-DD" of an instant in `timeZone`. */
export function dayKey(value: string | Date, timeZone: string): string {
  const date = typeof value === 'string' ? new Date(value) : value
  // en-CA formats dates as YYYY-MM-DD.
  return new Intl.DateTimeFormat('en-CA', { timeZone, year: 'numeric', month: '2-digit', day: '2-digit' }).format(date)
}

/** A "YYYY-MM-DD" key shifted by whole days (calendar arithmetic, no timezone involved). */
export function addDays(key: string, days: number): string {
  const [y, m, d] = key.split('-').map(Number)
  const date = new Date(Date.UTC(y, m - 1, d + days))
  return date.toISOString().slice(0, 10)
}

/** Day of week (0 = Sunday) of a "YYYY-MM-DD" key. */
export function weekdayOf(key: string): number {
  const [y, m, d] = key.split('-').map(Number)
  return new Date(Date.UTC(y, m - 1, d)).getUTCDay()
}

/** "Oct 10, 2026" (or "Oct 10" with short) for a "YYYY-MM-DD" key. */
export function formatDayKey(key: string, { short = false, weekday = false } = {}): string {
  const [y, m, d] = key.split('-').map(Number)
  return new Intl.DateTimeFormat(undefined, {
    timeZone: 'UTC',
    month: 'short',
    day: 'numeric',
    year: short ? undefined : 'numeric',
    weekday: weekday ? 'short' : undefined,
  }).format(new Date(Date.UTC(y, m - 1, d)))
}

/** "Today", "Yesterday" or a date, for a day key relative to today in the same zone. */
export function dayLabel(key: string, todayKey: string): string {
  if (key === todayKey) return 'Today'
  if (key === addDays(todayKey, -1)) return 'Yesterday'
  return formatDayKey(key, { weekday: true })
}

/** "Oct 10, 2026, 7:42 PM" in `timeZone`. */
export function formatDateTime(value: string, timeZone: string): string {
  return new Intl.DateTimeFormat(undefined, { timeZone, dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value))
}

/** "7:42 PM" in `timeZone`. */
export function formatTime(value: string, timeZone: string): string {
  return new Intl.DateTimeFormat(undefined, { timeZone, hour: 'numeric', minute: '2-digit' }).format(new Date(value))
}

const RELATIVE_STEPS: [Intl.RelativeTimeFormatUnit, number][] = [
  ['year', 365 * 24 * 3600],
  ['month', 30 * 24 * 3600],
  ['week', 7 * 24 * 3600],
  ['day', 24 * 3600],
  ['hour', 3600],
  ['minute', 60],
]

/** "2 minutes ago" / "just now" (an elapsed duration, so no timezone involved). */
export function timeAgo(value: string, now: number = Date.now()): string {
  const seconds = Math.round((new Date(value).getTime() - now) / 1000)
  const abs = Math.abs(seconds)
  if (abs < 45) return 'just now'
  const format = new Intl.RelativeTimeFormat(undefined, { numeric: 'auto' })
  for (const [unit, size] of RELATIVE_STEPS) {
    if (abs >= size) return format.format(Math.round(seconds / size), unit)
  }
  return format.format(Math.round(seconds / 60), 'minute')
}
