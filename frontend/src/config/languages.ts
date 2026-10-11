import type { Language } from '../types/problem'

/**
 * Coding languages the workspace knows how to edit. To add one later (C, Go,
 * Rust, ...): add it to the backend ProgrammingLanguage enum, add an entry
 * here, and register its Monaco grammar in workspace/monaco/monacoFeatures.js.
 * Which languages a problem offers comes from the backend (`languages`).
 */
export interface LanguageConfig {
  label: string
  /** Monaco language id. */
  monacoId: string
  /** Line comment prefix, used for placeholder text. */
  comment: string
}

export const LANGUAGE_CONFIG: Record<Language, LanguageConfig> = {
  CPP: { label: 'C++', monacoId: 'cpp', comment: '//' },
  JAVA: { label: 'Java', monacoId: 'java', comment: '//' },
  PYTHON: { label: 'Python', monacoId: 'python', comment: '#' },
}

/** Default language when a problem offers several (first available wins otherwise). */
export const DEFAULT_LANGUAGE: Language = 'CPP'
