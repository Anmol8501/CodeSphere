import { useSyncExternalStore } from 'react'

const subscribe = (onChange: () => void) => {
  document.addEventListener('fullscreenchange', onChange)
  return () => document.removeEventListener('fullscreenchange', onChange)
}

/**
 * Where overlays (modals, toasts) must render to stay visible: in native
 * fullscreen the browser only paints the fullscreen element's subtree.
 */
export function useOverlayRoot(): HTMLElement {
  return useSyncExternalStore(
    subscribe,
    () => (document.fullscreenElement as HTMLElement | null) ?? document.body,
    () => document.body,
  )
}
