import { useCallback, useState } from 'react'
import type { EditorSettings } from '../types/workspace'
import { DEFAULT_EDITOR_SETTINGS, editorSettingsStore } from '../utils/workspaceStorage'

/** Editor preferences, remembered in this browser (no sensitive data). */
export function useEditorSettings() {
  const [settings, setSettings] = useState<EditorSettings>(() => editorSettingsStore.get())

  const update = useCallback((patch: Partial<EditorSettings>) => {
    setSettings((current) => {
      const next = { ...current, ...patch }
      editorSettingsStore.set(next)
      return next
    })
  }, [])

  const reset = useCallback(() => {
    editorSettingsStore.set(DEFAULT_EDITOR_SETTINGS)
    setSettings(DEFAULT_EDITOR_SETTINGS)
  }, [])

  return { settings, update, reset }
}
