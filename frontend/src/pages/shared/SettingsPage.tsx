import { Check, KeyRound, LogOut, Monitor, Moon, Palette, ShieldCheck, Sun, UserRound } from 'lucide-react'
import { useState, type ReactNode } from 'react'
import { useNavigate } from 'react-router-dom'
import { Alert } from '../../components/ui/Alert'
import { Badge, RoleBadge } from '../../components/ui/Badge'
import { Button } from '../../components/ui/Button'
import { SectionCard } from '../../components/ui/Card'
import { PageHeader } from '../../components/ui/PageHeader'
import { useAuth } from '../../hooks/useAuth'
import { cn } from '../../utils/format'

type Theme = 'dark' | 'light'

const THEMES: { value: Theme; label: string; description: string; icon: typeof Moon; available: boolean }[] = [
  { value: 'dark', label: 'Dark', description: 'The CodeArena terminal theme.', icon: Moon, available: true },
  { value: 'light', label: 'Light', description: 'A light theme is planned.', icon: Sun, available: false },
]

function Row({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="flex flex-col gap-1 py-3.5 sm:flex-row sm:items-center sm:justify-between">
      <dt className="font-mono text-[11px] tracking-[0.16em] text-ink-400 uppercase">{label}</dt>
      <dd className="min-w-0 truncate text-sm font-semibold text-ink-950">{children}</dd>
    </div>
  )
}

export default function SettingsPage() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const [loggingOut, setLoggingOut] = useState(false)
  if (!user) return null

  // CodeArena currently ships one theme. The selector is real UI, but only
  // "Dark" can be chosen until the light theme exists.
  const theme: Theme = 'dark'

  const handleLogout = async () => {
    setLoggingOut(true)
    await logout()
    navigate('/login', { replace: true })
  }

  return (
    <div className="animate-fade-in">
      <PageHeader eyebrow="Account · Settings" title="Settings" description="Manage your preferences and account." />

      <div className="grid max-w-4xl gap-6">
        <SectionCard title="Appearance" description="Choose how CodeArena looks" icon={<Palette />}>
          <fieldset>
            <legend className="sr-only">Theme</legend>
            <div className="grid gap-3 sm:grid-cols-2">
              {THEMES.map((option) => {
                const Icon = option.icon
                const selected = option.value === theme
                return (
                  <label
                    key={option.value}
                    className={cn(
                      'relative flex items-start gap-3 rounded-xl border p-4 transition',
                      selected ? 'border-brand-500/50 bg-brand-500/[0.06]' : 'border-ink-200 bg-night/40',
                      option.available ? 'cursor-pointer' : 'cursor-not-allowed opacity-60',
                    )}
                  >
                    <input
                      type="radio"
                      name="theme"
                      value={option.value}
                      checked={selected}
                      disabled={!option.available}
                      onChange={() => undefined}
                      className="sr-only"
                    />
                    <span
                      className={cn(
                        'flex size-9 shrink-0 items-center justify-center rounded-lg ring-1',
                        selected ? 'bg-brand-500/10 text-brand-500 ring-brand-500/30' : 'bg-surface text-ink-400 ring-ink-200',
                      )}
                    >
                      <Icon className="size-[18px]" aria-hidden />
                    </span>
                    <span className="min-w-0 flex-1">
                      <span className="flex items-center gap-2 text-sm font-semibold text-ink-950">
                        {option.label}
                        {!option.available && (
                          <Badge tone="warning" mono>
                            Soon
                          </Badge>
                        )}
                      </span>
                      <span className="mt-0.5 block text-xs text-ink-500">{option.description}</span>
                    </span>
                    {selected && <Check className="size-4 text-brand-500" aria-label="Selected" />}
                  </label>
                )
              })}
            </div>
          </fieldset>
          <p className="mt-4 flex items-center gap-2 text-xs text-ink-400">
            <Monitor className="size-3.5" aria-hidden /> Animations are reduced automatically if your system asks for it.
          </p>
        </SectionCard>

        <SectionCard title="Account" description="Read-only account details" icon={<UserRound />}>
          <dl className="-my-3.5 divide-y divide-ink-200">
            <Row label="Name">{user.full_name}</Row>
            <Row label="Email">{user.email}</Row>
            <Row label="Role">
              <RoleBadge role={user.role} />
            </Row>
          </dl>
        </SectionCard>

        <SectionCard title="Security" description="Password and session" icon={<ShieldCheck />}>
          <div className="space-y-5">
            <div>
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <p className="text-sm font-semibold text-ink-950">Password</p>
                  <p className="text-xs text-ink-500">Change the password you use to sign in.</p>
                </div>
                <Button variant="secondary" size="sm" icon={<KeyRound className="size-4" aria-hidden />} disabled>
                  Change password
                </Button>
              </div>
              <Alert variant="info" className="mt-3">
                Password management will be available soon. Until then, contact your administrator to reset your
                password.
              </Alert>
            </div>
            <div className="flex flex-wrap items-center justify-between gap-3 border-t border-ink-200 pt-5">
              <div>
                <p className="text-sm font-semibold text-ink-950">Session</p>
                <p className="text-xs text-ink-500">You are signed in on this device.</p>
              </div>
              <Button
                variant="danger"
                size="sm"
                icon={<LogOut className="size-4" aria-hidden />}
                onClick={handleLogout}
                loading={loggingOut}
                loadingText="Logging out..."
              >
                Logout
              </Button>
            </div>
          </div>
        </SectionCard>
      </div>
    </div>
  )
}
