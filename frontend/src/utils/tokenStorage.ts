// The JWT access token is kept in localStorage so a page refresh keeps the
// user signed in. Access is wrapped in try/catch because storage can be
// unavailable (private mode, blocked site data).

export const TOKEN_STORAGE_KEY = 'codearena.access_token'

export const tokenStorage = {
  get(): string | null {
    try {
      return localStorage.getItem(TOKEN_STORAGE_KEY)
    } catch {
      return null
    }
  },
  set(token: string): void {
    try {
      localStorage.setItem(TOKEN_STORAGE_KEY, token)
    } catch {
      /* storage unavailable: user will need to log in again after refresh */
    }
  },
  clear(): void {
    try {
      localStorage.removeItem(TOKEN_STORAGE_KEY)
    } catch {
      /* ignore */
    }
  },
}
