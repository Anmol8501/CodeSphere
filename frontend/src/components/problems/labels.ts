import type { Difficulty, Language } from '../../types/problem'

export const DIFFICULTY_LABEL: Record<Difficulty, string> = { EASY: 'Easy', MEDIUM: 'Medium', HARD: 'Hard' }

/** Text color only (for counters and headings): Easy green, Medium yellow, Hard red. */
export const DIFFICULTY_TEXT: Record<Difficulty, string> = {
  EASY: 'text-brand-400',
  MEDIUM: 'text-warning',
  HARD: 'text-danger',
}

export const LANGUAGE_LABEL: Record<Language, string> = { CPP: 'C++', JAVA: 'Java', PYTHON: 'Python' }
