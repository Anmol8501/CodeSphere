import { ShieldAlert } from 'lucide-react'
import { Link } from 'react-router-dom'
import { useAuth } from '../../hooks/useAuth'
import { cn } from '../../utils/format'
import { ROLE_HOME } from '../../utils/routes'

/**
 * Shown when a logged-in user opens a page that belongs to another role.
 * `inline` renders it inside the app shell instead of as a full screen.
 */
export default function ForbiddenPage({ inline = false }: { inline?: boolean }) {
  const { user } = useAuth()

  return (
    <div
      className={cn(
        'flex items-center justify-center px-4',
        inline ? 'py-16' : 'bg-dot-grid-light min-h-svh bg-night',
      )}
    >
      <div className="w-full max-w-md animate-fade-in rounded-3xl border border-ink-200 bg-card p-8 text-center shadow-lift">
        <span className="mx-auto flex size-14 items-center justify-center rounded-2xl bg-danger/10 text-danger ring-1 ring-danger/25">
          <ShieldAlert className="size-7" aria-hidden />
        </span>
        <p className="mt-5 font-mono text-sm font-semibold text-danger">403 Forbidden</p>
        <h1 className="mt-1 text-xl font-extrabold text-ink-950">Access denied</h1>
        <p className="mt-2 text-sm text-ink-500">You are not authorized to access this page.</p>
        <Link
          to={user ? ROLE_HOME[user.role] : '/login'}
          className="mt-6 inline-flex h-10 items-center justify-center rounded-xl bg-brand-500 px-5 text-sm font-bold text-night shadow-glow transition hover:bg-brand-400"
        >
          {user ? 'Go to my dashboard' : 'Go to login'}
        </Link>
      </div>
    </div>
  )
}
