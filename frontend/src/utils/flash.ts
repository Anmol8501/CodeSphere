// One-time messages that survive a redirect (e.g. "Your session has expired").

const FLASH_KEY = 'codearena.flash'

export type FlashType = 'info' | 'success' | 'warning' | 'error'

export interface FlashMessage {
  type: FlashType
  message: string
}

export function setFlash(message: string, type: FlashType = 'info'): void {
  try {
    sessionStorage.setItem(FLASH_KEY, JSON.stringify({ type, message }))
  } catch {
    /* ignore */
  }
}

export function peekFlash(): FlashMessage | null {
  try {
    const raw = sessionStorage.getItem(FLASH_KEY)
    return raw ? (JSON.parse(raw) as FlashMessage) : null
  } catch {
    return null
  }
}

export function clearFlash(): void {
  try {
    sessionStorage.removeItem(FLASH_KEY)
  } catch {
    /* ignore */
  }
}
