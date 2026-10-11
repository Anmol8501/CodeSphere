import { useCallback, useEffect, useRef, useState } from 'react'
import { draftService } from '../services/draftService'
import type { Problem } from '../types/problem'
import type { Draft, SaveState, SupportedLanguage } from '../types/workspace'
import { getErrorStatus } from '../utils/errors'
import { draftBackup } from '../utils/workspaceStorage'

export const AUTOSAVE_DELAY_MS = 1000
const OFFLINE_RETRY_MS = 15_000

interface LanguageEntry {
  status: 'loading' | 'ready'
  /** Latest editor content. */
  code: string
  /** Content the server has confirmed (null = no saved draft yet / unknown). */
  savedCode: string | null
  /** Server draft version this content is based on (0 = none). */
  version: number
  starter: string
}

export interface DraftManager {
  /** The current language finished initializing; the editor may mount. */
  ready: boolean
  /** Content to create the editor model with (resolved draft or starter). */
  initialCode: string
  starterCode: string
  saveState: SaveState
  /** Non-fatal problem while loading, e.g. the saved draft could not be fetched. */
  loadWarning: string | null
  /** Unsynced changes restored from this browser on load. */
  restoredFromBackup: boolean
  onEditorChange: (code: string) => void
  /** Save the current language immediately (e.g. after Reset). */
  saveNow: () => Promise<boolean>
  retrySave: () => void
  /** 'server' returns the saved code to load into the editor; 'mine' overwrites it. */
  resolveConflict: (choice: 'server' | 'mine') => Promise<string | null>
  hasUnsavedChanges: () => boolean
  /** Save every language with pending changes. Resolves true when all are saved. */
  flushAll: () => Promise<boolean>
  /** Write unsaved changes to local backup synchronously (page unload). */
  backupAll: () => void
}

/** Has changes the server has not confirmed (untouched starter code is not "unsaved"). */
function isDirty(entry: LanguageEntry): boolean {
  return entry.status === 'ready' && entry.code !== (entry.savedCode ?? entry.starter)
}

/** State for content the server already has (or untouched starter code). */
function cleanState(entry: LanguageEntry): SaveState {
  return entry.savedCode === null ? 'idle' : 'saved'
}

/**
 * Initialization order (never lets starter code overwrite a saved draft):
 *   1. fetch the user's draft for (problem, language)
 *   2. resolve initial code: draft > local unsynced backup > starter code
 *   3. mark ready (the editor mounts with that code)
 *   4. only then do edits schedule a debounced autosave
 */
export function useDraftManager(userId: number, problem: Problem, language: SupportedLanguage): DraftManager {
  const entries = useRef(new Map<SupportedLanguage, LanguageEntry>())
  const inflight = useRef(new Map<SupportedLanguage, Promise<boolean>>())
  const pending = useRef(new Set<SupportedLanguage>())
  const timers = useRef(new Map<SupportedLanguage, number>())
  const statesRef = useRef(new Map<SupportedLanguage, SaveState>())
  const [states, setStates] = useState<Partial<Record<SupportedLanguage, SaveState>>>({})
  const [warnings, setWarnings] = useState<Partial<Record<SupportedLanguage, string>>>({})
  const [restored, setRestored] = useState<Partial<Record<SupportedLanguage, boolean>>>({})
  // Code each language was initialized with (state, so render never reads refs).
  const [loadedCode, setLoadedCode] = useState<Partial<Record<SupportedLanguage, string>>>({})

  const setState = useCallback((lang: SupportedLanguage, state: SaveState) => {
    statesRef.current.set(lang, state)
    setStates((current) => (current[lang] === state ? current : { ...current, [lang]: state }))
  }, [])

  const starterFor = useCallback(
    (lang: SupportedLanguage) => problem.starter_codes.find((s) => s.language === lang)?.starter_code ?? '',
    [problem.starter_codes],
  )

  const clearTimer = (lang: SupportedLanguage) => {
    const timer = timers.current.get(lang)
    if (timer !== undefined) window.clearTimeout(timer)
    timers.current.delete(lang)
  }

  // Latest `save`, for timers and callbacks created before it changed.
  const saveRef = useRef<(lang: SupportedLanguage, force?: boolean) => Promise<boolean>>(() => Promise.resolve(true))

  // ---------------------------------------------------------------- saving
  const save = useCallback(
    (lang: SupportedLanguage, force = false): Promise<boolean> => {
      const entry = entries.current.get(lang)
      if (!entry || entry.status !== 'ready') return Promise.resolve(true)
      const running = inflight.current.get(lang)
      if (running) {
        pending.current.add(lang)
        return running
      }
      clearTimer(lang)
      if (!force && !isDirty(entry)) {
        setState(lang, cleanState(entry))
        return Promise.resolve(true)
      }

      const code = entry.code
      // Keep a local copy until the server confirms (offline / crash safety).
      draftBackup.set(userId, problem.id, lang, code, entry.version)
      setState(lang, 'saving')
      const request = draftService
        .save(problem.id, { language: lang, source_code: code, base_version: entry.version, force })
        .then((result) => {
          entry.version = result.version
          entry.savedCode = code
          if (entry.code === code) {
            draftBackup.clear(userId, problem.id, lang)
            setState(lang, 'saved')
          } else {
            setState(lang, 'unsaved')
          }
          return true
        })
        .catch((error: unknown) => {
          const status = getErrorStatus(error)
          setState(lang, status === 409 ? 'conflict' : status === undefined ? 'offline' : 'error')
          return false
        })
        .finally(() => {
          inflight.current.delete(lang)
          if (pending.current.delete(lang) && statesRef.current.get(lang) === 'unsaved') void saveRef.current(lang)
        })
      inflight.current.set(lang, request)
      return request
    },
    [problem.id, userId, setState],
  )

  useEffect(() => {
    saveRef.current = save
  }, [save])

  // ---------------------------------------------------------------- loading
  const applyLoaded = useCallback(
    (lang: SupportedLanguage, draft: Draft | null | undefined, failed: boolean) => {
      const starter = starterFor(lang)
      const backup = draftBackup.get(userId, problem.id, lang)
      let code: string
      let savedCode: string | null = null
      let version = 0
      let restoredLocal = false

      if (failed) {
        code = backup?.code ?? starter
        version = backup?.baseVersion ?? 0
        setWarnings((w) => ({
          ...w,
          [lang]: `Unable to load saved draft. ${backup ? 'Showing the copy kept in this browser.' : 'Showing the starter code.'}`,
        }))
      } else {
        version = draft?.version ?? 0
        savedCode = draft?.source_code ?? null
        code = savedCode ?? starter
        if (backup && backup.baseVersion === version && backup.code !== code) {
          // Unsynced edits from an earlier session on top of the same server version.
          code = backup.code
          restoredLocal = true
        } else if (backup) {
          draftBackup.clear(userId, problem.id, lang) // already synced, or superseded by a newer save
        }
      }

      const entry: LanguageEntry = { status: 'ready', code, savedCode, version, starter }
      entries.current.set(lang, entry)
      setState(lang, isDirty(entry) ? 'unsaved' : cleanState(entry))
      if (restoredLocal) {
        setRestored((r) => ({ ...r, [lang]: true }))
        window.setTimeout(() => void saveRef.current(lang), 0)
      }
      setLoadedCode((current) => ({ ...current, [lang]: code }))
    },
    [problem.id, userId, starterFor, setState],
  )

  useEffect(() => {
    if (entries.current.has(language)) return
    entries.current.set(language, { status: 'loading', code: '', savedCode: null, version: 0, starter: starterFor(language) })
    setState(language, 'initializing')
    // Not cancelled on language switch: the result is cached for that language.
    draftService
      .get(problem.id, language)
      .then((draft) => applyLoaded(language, draft, false))
      .catch(() => applyLoaded(language, undefined, true))
  }, [problem.id, language, starterFor, applyLoaded, setState])

  // Switching language flushes pending edits of the previous one immediately
  // and remembers its latest code, used if its editor model is recreated.
  useEffect(
    () => () => {
      const entry = entries.current.get(language)
      if (entry?.status === 'ready') setLoadedCode((current) => ({ ...current, [language]: entry.code }))
      void saveRef.current(language)
    },
    [language],
  )

  // ---------------------------------------------------------------- offline retry
  useEffect(() => {
    const retryOffline = () => {
      statesRef.current.forEach((state, lang) => {
        if (state === 'offline') void saveRef.current(lang)
      })
    }
    window.addEventListener('online', retryOffline)
    const interval = window.setInterval(retryOffline, OFFLINE_RETRY_MS)
    return () => {
      window.removeEventListener('online', retryOffline)
      window.clearInterval(interval)
    }
  }, [])

  // Leaving the workspace: stop timers and push any pending edits.
  useEffect(() => {
    const timerMap = timers.current
    const entryMap = entries.current
    return () => {
      timerMap.forEach((timer) => window.clearTimeout(timer))
      timerMap.clear()
      entryMap.forEach((_, lang) => void saveRef.current(lang))
    }
  }, [])

  // ---------------------------------------------------------------- public API
  const onEditorChange = useCallback(
    (code: string) => {
      const entry = entries.current.get(language)
      if (!entry || entry.status !== 'ready' || entry.code === code) return
      entry.code = code
      if (statesRef.current.get(language) === 'conflict') {
        // Autosave pauses until the student resolves the conflict; keep a local copy.
        draftBackup.set(userId, problem.id, language, code, entry.version)
        return
      }
      setState(language, isDirty(entry) ? 'unsaved' : cleanState(entry))
      clearTimer(language)
      timers.current.set(
        language,
        window.setTimeout(() => void saveRef.current(language), AUTOSAVE_DELAY_MS),
      )
    },
    [language, problem.id, userId, setState],
  )

  const resolveConflict = useCallback(
    async (choice: 'server' | 'mine'): Promise<string | null> => {
      const entry = entries.current.get(language)
      if (!entry) return null
      if (choice === 'mine') {
        await saveRef.current(language, true)
        return null
      }
      try {
        const draft = await draftService.get(problem.id, language)
        const code = draft?.source_code ?? entry.starter
        entry.version = draft?.version ?? 0
        entry.savedCode = draft?.source_code ?? null
        entry.code = code
        draftBackup.clear(userId, problem.id, language)
        setState(language, cleanState(entry))
        return code
      } catch {
        setState(language, 'conflict')
        return null
      }
    },
    [language, problem.id, userId, setState],
  )

  const hasUnsavedChanges = useCallback(() => {
    for (const [lang, entry] of entries.current) {
      if (isDirty(entry) || inflight.current.has(lang)) return true
    }
    return false
  }, [])

  const flushAll = useCallback(async () => {
    const results = await Promise.all([...entries.current.keys()].map((lang) => saveRef.current(lang)))
    return results.every(Boolean) && !hasUnsavedChanges()
  }, [hasUnsavedChanges])

  const backupAll = useCallback(() => {
    entries.current.forEach((entry, lang) => {
      if (isDirty(entry)) draftBackup.set(userId, problem.id, lang, entry.code, entry.version)
    })
  }, [userId, problem.id])

  const initialCode = loadedCode[language]
  return {
    ready: initialCode !== undefined,
    initialCode: initialCode ?? '',
    starterCode: starterFor(language),
    saveState: states[language] ?? 'initializing',
    loadWarning: warnings[language] ?? null,
    restoredFromBackup: restored[language] ?? false,
    onEditorChange,
    saveNow: () => saveRef.current(language),
    retrySave: () => void saveRef.current(language),
    resolveConflict,
    hasUnsavedChanges,
    flushAll,
    backupAll,
  }
}
