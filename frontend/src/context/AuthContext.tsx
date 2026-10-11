import { useCallback, useEffect, useMemo, useState, type ReactNode } from 'react'
import { SESSION_EXPIRED_EVENT } from '../services/api'
import { authService } from '../services/authService'
import type { LoginCredentials, LoginPortal, RegisterPayload, User } from '../types/auth'
import { SESSION_EXPIRED_MESSAGE } from '../utils/errors'
import { setFlash } from '../utils/flash'
import { getTokenExpiry } from '../utils/jwt'
import { TOKEN_STORAGE_KEY, tokenStorage } from '../utils/tokenStorage'
import { AuthContext, type AuthContextValue } from './authContextValue'

const MAX_TIMEOUT_MS = 2_147_483_647 // setTimeout limit (~24.8 days)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  const endSession = useCallback((message?: string) => {
    tokenStorage.clear()
    if (message) setFlash(message, 'warning')
    setUser(null)
  }, [])

  const refreshUser = useCallback(async (): Promise<User | null> => {
    if (!tokenStorage.get()) {
      setUser(null)
      return null
    }
    try {
      const current = await authService.me()
      setUser(current)
      return current
    } catch {
      // A 401 is already handled by the API interceptor (session expired event).
      tokenStorage.clear()
      setUser(null)
      return null
    }
  }, [])

  // On first load (or a browser refresh) restore the session from the stored token.
  useEffect(() => {
    refreshUser().finally(() => setLoading(false))
  }, [refreshUser])

  // The API layer fires this event when the backend rejects our token.
  useEffect(() => {
    const onExpired = (event: Event) => {
      const message = (event as CustomEvent<string>).detail || SESSION_EXPIRED_MESSAGE
      endSession(message)
    }
    window.addEventListener(SESSION_EXPIRED_EVENT, onExpired)
    return () => window.removeEventListener(SESSION_EXPIRED_EVENT, onExpired)
  }, [endSession])

  // Log out automatically the moment the token expires, even without an API call.
  useEffect(() => {
    if (!user) return
    const token = tokenStorage.get()
    const expiry = token ? getTokenExpiry(token) : null
    if (!expiry) return
    const msLeft = expiry * 1000 - Date.now()
    if (msLeft <= 0) {
      endSession(SESSION_EXPIRED_MESSAGE)
      return
    }
    const timer = window.setTimeout(
      () => endSession(SESSION_EXPIRED_MESSAGE),
      Math.min(msLeft, MAX_TIMEOUT_MS),
    )
    return () => window.clearTimeout(timer)
  }, [user, endSession])

  // Keep multiple browser tabs in sync (logout in one tab logs out the others).
  useEffect(() => {
    const onStorage = (event: StorageEvent) => {
      if (event.key !== TOKEN_STORAGE_KEY) return
      if (event.newValue) void refreshUser()
      else setUser(null)
    }
    window.addEventListener('storage', onStorage)
    return () => window.removeEventListener('storage', onStorage)
  }, [refreshUser])

  const login = useCallback(async (credentials: LoginCredentials, portal: LoginPortal) => {
    const data = await authService.login(credentials, portal)
    tokenStorage.set(data.access_token)
    setUser(data.user)
    return data.user
  }, [])

  // Registration does not log the user in; they are sent to the login page.
  const register = useCallback((payload: RegisterPayload) => authService.register(payload), [])

  const logout = useCallback(async () => {
    try {
      if (tokenStorage.get()) await authService.logout()
    } catch {
      /* the token is discarded locally either way */
    } finally {
      tokenStorage.clear()
      setUser(null)
    }
  }, [])

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      isAuthenticated: user !== null,
      loading,
      login,
      register,
      logout,
      refreshUser,
    }),
    [user, loading, login, register, logout, refreshUser],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
