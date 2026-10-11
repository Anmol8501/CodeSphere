import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { FullPageLoader } from '../components/ui/FullPageLoader'
import { useAuth } from '../hooks/useAuth'
import { getPostLoginPath } from '../utils/routes'

/**
 * Wraps login/register pages. Logged-in users are sent to their dashboard
 * (or the page they originally asked for). This is also what performs the
 * redirect right after a successful login.
 */
export function GuestRoute() {
  const { user, loading } = useAuth()
  const location = useLocation()

  if (loading) return <FullPageLoader message="Loading..." />

  if (user) {
    const from = (location.state as { from?: string } | null)?.from
    return <Navigate to={getPostLoginPath(user, from)} replace />
  }

  return <Outlet />
}
