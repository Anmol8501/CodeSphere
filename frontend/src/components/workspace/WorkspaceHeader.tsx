import { ArrowLeft, Maximize2, Minimize2 } from 'lucide-react'
import type { MouseEvent } from 'react'
import { Link } from 'react-router-dom'
import type { User } from '../../types/auth'
import type { Problem } from '../../types/problem'
import type { EditorSettings, SaveState, SupportedLanguage } from '../../types/workspace'
import { LogoMark } from '../brand/Logo'
import { ProfileDropdown } from '../layout/ProfileDropdown'
import { DifficultyBadge } from '../problems/DifficultyBadge'
import { EditorSettingsMenu } from './EditorSettingsMenu'
import { LanguageSelector } from './LanguageSelector'
import { SaveStatus } from './SaveStatus'

interface WorkspaceHeaderProps {
  user: User
  problem: Problem
  problemPath: string
  language: SupportedLanguage
  onLanguageChange: (language: SupportedLanguage) => void
  saveState: SaveState
  onRetrySave: () => void
  settings: EditorSettings
  onSettingsChange: (patch: Partial<EditorSettings>) => void
  onSettingsReset: () => void
  fullscreen: boolean
  onToggleFullscreen: () => void
  /** Intercepts in-app navigation so unsaved code is flushed first. */
  onNavigate: (event: MouseEvent<HTMLAnchorElement>, to: string) => void
  onLogout: () => void
  loggingOut: boolean
}

export function WorkspaceHeader({
  user,
  problem,
  problemPath,
  language,
  onLanguageChange,
  saveState,
  onRetrySave,
  settings,
  onSettingsChange,
  onSettingsReset,
  fullscreen,
  onToggleFullscreen,
  onNavigate,
  onLogout,
  loggingOut,
}: WorkspaceHeaderProps) {
  return (
    <header className="flex shrink-0 flex-wrap items-center gap-x-3 gap-y-2 border-b border-ink-200 bg-surface px-3 py-2 lg:h-14 lg:flex-nowrap lg:py-0">
      <div className="flex min-w-0 flex-1 items-center gap-2.5">
        <Link
          to="/student/dashboard"
          onClick={(e) => onNavigate(e, '/student/dashboard')}
          aria-label="CodeArena dashboard"
          className="flex shrink-0 items-center gap-2 rounded-lg"
        >
          <LogoMark className="size-8" />
          <span className="hidden font-mono text-sm font-extrabold tracking-wider text-ink-950 xl:inline">
            CODE<span className="text-brand-500">ARENA</span>
          </span>
        </Link>
        <span className="h-6 w-px shrink-0 bg-ink-200" aria-hidden />
        <Link
          to={problemPath}
          onClick={(e) => onNavigate(e, problemPath)}
          className="inline-flex shrink-0 items-center gap-1.5 rounded-lg px-1.5 py-1 text-sm font-semibold text-ink-500 transition hover:text-brand-400"
        >
          <ArrowLeft className="size-4" aria-hidden />
          <span className="hidden sm:inline">Back to Problem</span>
          <span className="sm:hidden">Back</span>
        </Link>
        <div className="flex min-w-0 items-center gap-2">
          <p className="truncate text-sm font-bold text-ink-950" title={problem.title}>
            {problem.title}
          </p>
          <DifficultyBadge difficulty={problem.difficulty} className="hidden shrink-0 sm:inline-flex" />
        </div>
      </div>

      <div className="flex w-full items-center justify-between gap-2 lg:w-auto lg:justify-end">
        <SaveStatus state={saveState} onRetry={onRetrySave} />
        <div className="flex items-center gap-2">
          <LanguageSelector
            className="w-28"
            languages={problem.languages}
            value={language}
            onChange={onLanguageChange}
          />
          <EditorSettingsMenu settings={settings} onChange={onSettingsChange} onReset={onSettingsReset} />
          <button
            type="button"
            onClick={onToggleFullscreen}
            aria-label={fullscreen ? 'Exit fullscreen' : 'Enter fullscreen'}
            aria-pressed={fullscreen}
            title={fullscreen ? 'Exit fullscreen (Esc)' : 'Fullscreen'}
            className="flex size-9 items-center justify-center rounded-lg text-ink-500 ring-1 ring-ink-200 transition hover:text-ink-950 hover:ring-brand-500/40"
          >
            {fullscreen ? <Minimize2 className="size-4" aria-hidden /> : <Maximize2 className="size-4" aria-hidden />}
          </button>
          <ProfileDropdown user={user} onLogout={onLogout} loggingOut={loggingOut} />
        </div>
      </div>
    </header>
  )
}
