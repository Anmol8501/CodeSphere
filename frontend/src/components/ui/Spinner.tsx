import { Loader2 } from 'lucide-react'
import { cn } from '../../utils/format'

export function Spinner({ className }: { className?: string }) {
  return <Loader2 className={cn('size-5 animate-spin text-brand-500', className)} aria-hidden />
}
