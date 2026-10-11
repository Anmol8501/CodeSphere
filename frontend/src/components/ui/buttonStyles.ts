import { cn } from '../../utils/format'

export type Variant = 'primary' | 'secondary' | 'ghost' | 'danger' | 'success' | 'dark'
export type Size = 'sm' | 'md' | 'lg'

const VARIANTS: Record<Variant, string> = {
  primary: 'bg-brand-500 font-bold text-night shadow-glow hover:bg-brand-400',
  secondary: 'bg-surface text-ink-800 ring-1 ring-inset ring-ink-200 hover:bg-ink-100 hover:ring-brand-500/40',
  ghost: 'text-ink-500 hover:bg-ink-100 hover:text-ink-950',
  danger: 'bg-transparent text-danger ring-1 ring-inset ring-danger/40 hover:bg-danger/10',
  success: 'bg-transparent text-brand-400 ring-1 ring-inset ring-brand-500/40 hover:bg-brand-500/10',
  dark: 'bg-night text-ink-950 ring-1 ring-inset ring-ink-200 hover:bg-ink-100',
}

const SIZES: Record<Size, string> = {
  sm: 'h-8 gap-1.5 rounded-lg px-3 text-xs',
  md: 'h-10 gap-2 rounded-xl px-4 text-sm',
  lg: 'h-12 gap-2 rounded-xl px-5 text-[15px]',
}

/** Shared class builder so links can look exactly like buttons. */
export function buttonClasses(variant: Variant = 'primary', size: Size = 'md', fullWidth?: boolean) {
  return cn(
    'inline-flex items-center justify-center font-semibold whitespace-nowrap transition-colors',
    'disabled:cursor-not-allowed disabled:opacity-50 aria-disabled:cursor-not-allowed aria-disabled:opacity-50',
    VARIANTS[variant],
    SIZES[size],
    fullWidth && 'w-full',
  )
}
