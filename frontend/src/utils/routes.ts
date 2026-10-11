import type { Role, User } from '../types/auth'

/** Where each role lands after logging in. */
export const ROLE_HOME: Record<Role, string> = {
  STUDENT: '/student/dashboard',
  STAFF: '/staff/dashboard',
  ADMIN: '/admin/dashboard',
}

const ROLE_AREA: Record<Role, string> = {
  STUDENT: '/student/',
  STAFF: '/staff/',
  ADMIN: '/admin/',
}

export const ROLE_PROFILE: Record<Role, string> = {
  STUDENT: '/student/profile',
  STAFF: '/staff/profile',
  ADMIN: '/admin/profile',
}

/**
 * After login, return the user to the page they originally requested, but only
 * if it belongs to their own role area. Otherwise send them to their dashboard.
 */
export function getPostLoginPath(user: User, requestedPath?: string | null): string {
  if (
    requestedPath &&
    requestedPath.startsWith(ROLE_AREA[user.role]) &&
    !requestedPath.startsWith('/admin/login')
  ) {
    return requestedPath
  }
  return ROLE_HOME[user.role]
}
