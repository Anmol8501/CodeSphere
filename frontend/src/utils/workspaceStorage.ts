/**
 * Browser-local workspace data. Never authoritative: PostgreSQL holds drafts.
 * Keys include the user id so people sharing a browser never see each
 * other's local data. No tokens or other sensitive values are stored here.
 */
import type { CustomTestCase, EditorSettings, SupportedLanguage } from '../types/workspace'

const PREFIX = 'codearena.'

function read<T>(key: string): T | null {
  try {
    const raw = localStorage.getItem(PREFIX + key)
    return raw ? (JSON.parse(raw) as T) : null
  } catch {
    return null
  }
}

function write(key: string, value: unknown): void {
  try {
    localStorage.setItem(PREFIX + key, JSON.stringify(value))
  } catch {
    /* storage full or blocked: local backup is best-effort */
  }
}

function remove(key: string): void {
  try {
    localStorage.removeItem(PREFIX + key)
  } catch {
    /* ignore */
  }
}

// ------------------------------------------------------------------ draft backup
/** Unsaved code kept locally until the server confirms the save. */
export interface DraftBackup {
  code: string
  /** Server draft version the code was based on. */
  baseVersion: number
  savedAt: string
}

const backupKey = (userId: number, problemId: number, language: SupportedLanguage) =>
  `draft-backup.${userId}.${problemId}.${language}`

export const draftBackup = {
  get: (userId: number, problemId: number, language: SupportedLanguage) =>
    read<DraftBackup>(backupKey(userId, problemId, language)),
  set: (userId: number, problemId: number, language: SupportedLanguage, code: string, baseVersion: number) =>
    write(backupKey(userId, problemId, language), { code, baseVersion, savedAt: new Date().toISOString() }),
  clear: (userId: number, problemId: number, language: SupportedLanguage) => remove(backupKey(userId, problemId, language)),
}

// ------------------------------------------------------------------ preferences
export const DEFAULT_EDITOR_SETTINGS: EditorSettings = {
  fontSize: 14,
  theme: 'codearena-dark',
  wordWrap: false,
  minimap: false,
  tabSize: 4,
}

export const editorSettingsStore = {
  get(): EditorSettings {
    const saved = read<Partial<EditorSettings>>('editor-settings') ?? {}
    return { ...DEFAULT_EDITOR_SETTINGS, ...saved }
  },
  set: (settings: EditorSettings) => write('editor-settings', settings),
}

export const splitStore = {
  get: (): number | null => read<number>('workspace-split'),
  set: (percent: number) => write('workspace-split', percent),
}

export const languagePreference = {
  get: (userId: number) => read<SupportedLanguage>(`workspace-language.${userId}`),
  set: (userId: number, language: SupportedLanguage) => write(`workspace-language.${userId}`, language),
}

// ------------------------------------------------------------------ custom tests
const customKey = (userId: number, problemId: number) => `custom-tests.${userId}.${problemId}`

export const customTestStore = {
  get: (userId: number, problemId: number) => read<CustomTestCase[]>(customKey(userId, problemId)) ?? [],
  set: (userId: number, problemId: number, cases: CustomTestCase[]) => write(customKey(userId, problemId), cases),
}
