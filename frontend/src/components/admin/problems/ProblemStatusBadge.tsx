import type { ProblemStatus } from '../../../types/problem'
import { cn } from '../../../utils/format'
import { Badge } from '../../ui/Badge'
import { TONE_DOT, type Tone } from '../../ui/tones'

const CONFIG: Record<ProblemStatus, { label: string; tone: Tone }> = {
  PUBLISHED: { label: 'Published', tone: 'brand' },
  DRAFT: { label: 'Draft', tone: 'warning' },
  ARCHIVED: { label: 'Archived', tone: 'neutral' },
}

export function ProblemStatusBadge({ status }: { status: ProblemStatus }) {
  const { label, tone } = CONFIG[status]
  return (
    <Badge tone={tone}>
      <span className={cn('size-1.5 rounded-full', TONE_DOT[tone])} aria-hidden />
      {label}
    </Badge>
  )
}
