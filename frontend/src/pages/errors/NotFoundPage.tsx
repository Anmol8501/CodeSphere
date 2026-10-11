import { Link } from 'react-router-dom'
import { LogoMark } from '../../components/brand/Logo'
import { useAuth } from '../../hooks/useAuth'
import { ROLE_HOME } from '../../utils/routes'

export default function NotFoundPage() {
  const { user } = useAuth()

  return (
    <div className="bg-dot-grid-light flex min-h-svh flex-col items-center justify-center bg-night px-4 text-center">
      <LogoMark className="size-12" />
      <p className="mt-6 font-mono text-6xl font-bold text-brand-500/30">404</p>
      <h1 className="mt-2 text-xl font-extrabold text-ink-950">Page not found</h1>
      <p className="mt-2 max-w-sm text-sm text-ink-500">
        <span className="font-mono text-brand-600">return null;</span> The page you're looking for doesn't exist.
      </p>
      <Link
        to={user ? ROLE_HOME[user.role] : '/'}
        className="mt-6 inline-flex h-10 items-center rounded-xl bg-brand-500 px-5 text-sm font-bold text-night shadow-glow transition hover:bg-brand-400"
      >
        {user ? 'Back to dashboard' : 'Back to home'}
      </Link>
    </div>
  )
}
