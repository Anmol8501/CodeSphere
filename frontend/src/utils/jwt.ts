/**
 * Read the `exp` claim (seconds since epoch) from a JWT without verifying it.
 * Used only to log the user out when the token expires; the backend is the
 * real authority on whether a token is valid.
 */
export function getTokenExpiry(token: string): number | null {
  try {
    const payloadPart = token.split('.')[1]
    if (!payloadPart) return null
    const base64 = payloadPart.replace(/-/g, '+').replace(/_/g, '/')
    const payload = JSON.parse(atob(base64)) as { exp?: unknown }
    return typeof payload.exp === 'number' ? payload.exp : null
  } catch {
    return null
  }
}
