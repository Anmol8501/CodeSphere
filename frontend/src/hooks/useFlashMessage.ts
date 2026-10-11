import { useEffect, useState } from 'react'
import { clearFlash, peekFlash, type FlashMessage } from '../utils/flash'

/**
 * Read a one-time flash message (e.g. "session expired") once, then clear it.
 * Reading happens in the state initializer and clearing in an effect, which
 * keeps it safe under React StrictMode's double rendering.
 */
export function useFlashMessage(): FlashMessage | null {
  const [flash] = useState<FlashMessage | null>(() => peekFlash())
  useEffect(() => {
    if (flash) clearFlash()
  }, [flash])
  return flash
}
