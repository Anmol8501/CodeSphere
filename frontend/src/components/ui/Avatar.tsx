import { cn, getInitials } from '../../utils/format'

type Size = 'sm' | 'md' | 'lg' | 'xl'

const SIZES: Record<Size, string> = {
  sm: 'size-8 text-[11px]',
  md: 'size-9 text-xs',
  lg: 'size-12 text-sm',
  xl: 'size-20 text-2xl',
}

interface AvatarProps {
  name: string
  size?: Size
  className?: string
  /** Muted variant for lists (neutral background instead of brand gradient). */
  muted?: boolean
}

/** Initials avatar. Profile photos are not stored in Phase 2. */
export function Avatar({ name, size = 'md', className, muted }: AvatarProps) {
  return (
    <span
      className={cn(
        'inline-flex shrink-0 items-center justify-center rounded-full font-bold select-none',
        muted
          ? 'bg-ink-100 text-ink-500 ring-1 ring-ink-200'
          : 'bg-gradient-to-br from-brand-500 to-accent text-night',
        SIZES[size],
        className,
      )}
      aria-hidden
    >
      {getInitials(name)}
    </span>
  )
}
