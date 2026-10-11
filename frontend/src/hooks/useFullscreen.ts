import { useCallback, useEffect, useState, type RefObject } from 'react'

/**
 * Fullscreen for one element. Uses the browser Fullscreen API (Esc exits
 * natively); where it is unavailable, falls back to an in-page overlay that
 * Esc also closes.
 */
export function useFullscreen(ref: RefObject<HTMLElement | null>) {
  const [nativeActive, setNativeActive] = useState(false)
  const [fallbackActive, setFallbackActive] = useState(false)

  useEffect(() => {
    const onChange = () => setNativeActive(document.fullscreenElement !== null && document.fullscreenElement === ref.current)
    document.addEventListener('fullscreenchange', onChange)
    return () => document.removeEventListener('fullscreenchange', onChange)
  }, [ref])

  useEffect(() => {
    if (!fallbackActive) return
    const onKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') setFallbackActive(false)
    }
    document.addEventListener('keydown', onKey)
    return () => document.removeEventListener('keydown', onKey)
  }, [fallbackActive])

  const exit = useCallback(async () => {
    setFallbackActive(false)
    if (document.fullscreenElement) await document.exitFullscreen().catch(() => {})
  }, [])

  const enter = useCallback(async () => {
    const element = ref.current
    if (!element) return
    if (document.fullscreenEnabled && element.requestFullscreen) {
      try {
        await element.requestFullscreen()
        return
      } catch {
        /* blocked (e.g. iframe policy): use the overlay instead */
      }
    }
    setFallbackActive(true)
  }, [ref])

  const active = nativeActive || fallbackActive
  const toggle = useCallback(() => (active ? exit() : enter()), [active, enter, exit])

  return { active, fallbackActive, enter, exit, toggle }
}
