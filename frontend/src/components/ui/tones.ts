/** Semantic color tones shared by badges, stat cards and status indicators. */
export type Tone = 'brand' | 'accent' | 'warning' | 'danger' | 'info' | 'neutral'

/** Soft tinted chip: background + text + ring. */
export const TONE_CHIP: Record<Tone, string> = {
  brand: 'bg-brand-500/10 text-brand-400 ring-brand-500/30',
  accent: 'bg-accent/10 text-accent ring-accent/30',
  warning: 'bg-warning/10 text-warning ring-warning/30',
  danger: 'bg-danger/10 text-danger ring-danger/30',
  info: 'bg-info/10 text-info ring-info/30',
  neutral: 'bg-ink-100 text-ink-500 ring-ink-200',
}

/** Solid dot color. */
export const TONE_DOT: Record<Tone, string> = {
  brand: 'bg-brand-500',
  accent: 'bg-accent',
  warning: 'bg-warning',
  danger: 'bg-danger',
  info: 'bg-info',
  neutral: 'bg-ink-400',
}
