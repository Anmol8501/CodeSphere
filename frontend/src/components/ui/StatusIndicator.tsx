import { cn } from '../../utils/format'
import type { Tone } from './tones'
import { TONE_DOT } from './tones'

export type ServiceState = 'online' | 'offline' | 'not_connected' | 'coming_soon'

const STATES: Record<ServiceState, { label: string; tone: Tone; text: string }> = {
  online: { label: 'Online', tone: 'brand', text: 'text-brand-500' },
  offline: { label: 'Offline', tone: 'danger', text: 'text-danger' },
  not_connected: { label: 'Not connected', tone: 'neutral', text: 'text-ink-500' },
  coming_soon: { label: 'Coming soon', tone: 'warning', text: 'text-warning' },
}

export function StatusIndicator({ state, className }: { state: ServiceState; className?: string }) {
  const s = STATES[state]
  return (
    <span className={cn('inline-flex items-center gap-2 font-mono text-[11px] font-semibold tracking-wider uppercase', s.text, className)}>
      <span className="relative flex size-2" aria-hidden>
        {state === 'online' && (
          <span className="absolute inline-flex size-full animate-ping rounded-full bg-brand-500 opacity-50" />
        )}
        <span className={cn('relative inline-flex size-2 rounded-full', TONE_DOT[s.tone])} />
      </span>
      {s.label}
    </span>
  )
}
