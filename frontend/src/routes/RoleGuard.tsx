import { Outlet } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import ForbiddenPage from '../pages/errors/ForbiddenPage'
import type { Role } from '../types/auth'

/**
 * Role check for pages that live inside the authenticated layout.
 * (ProtectedRoute above it already handles logged-out users.) Frontend only:
 * the backend independently enforces roles on every API call.
 */
export function RoleGuard({ roles, fullPage = false }: { roles: Role[]; fullPage?: boolean }) {
  const { user } = useAuth()
  // `fullPage` for routes rendered outside the app shell (e.g. the coding workspace).
  if (!user || !roles.includes(user.role)) return <ForbiddenPage inline={!fullPage} />
  return <Outlet />
}
