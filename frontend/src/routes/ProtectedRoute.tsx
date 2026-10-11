import type { ReactNode } from 'react'
import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { FullPageLoader } from '../components/ui/FullPageLoader'
import { useAuth } from '../hooks/useAuth'
import ForbiddenPage from '../pages/errors/ForbiddenPage'
import type { Role } from '../types/auth'

interface ProtectedRouteProps {
  allowedRoles: Role[]
  children?: ReactNode
}

/**
 * Frontend guard for role-specific pages. This only improves UX: every API
 * endpoint enforces the same rules on the backend.
 */
export function ProtectedRoute({ allowedRoles, children }: ProtectedRouteProps) {
  const { user, loading } = useAuth()
  const location = useLocation()

  if (loading) return <FullPageLoader message="Loading dashboard..." />

  if (!user) {
    const loginPath = location.pathname.startsWith('/admin') ? '/admin/login' : '/login'
    return (
      <Navigate to={loginPath} replace state={{ from: location.pathname + location.search }} />
    )
  }

  if (!allowedRoles.includes(user.role)) return <ForbiddenPage />

  return children ?? <Outlet />
}
