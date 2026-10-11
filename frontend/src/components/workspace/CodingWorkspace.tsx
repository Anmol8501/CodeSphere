import { Minimize2 } from 'lucide-react'
import { useCallback, useEffect, useRef, useState, type MouseEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { DEFAULT_LANGUAGE, LANGUAGE_CONFIG } from '../../config/languages'
import { useAuth } from '../../hooks/useAuth'
import { useDraftManager } from '../../hooks/useDraftManager'
import { useEditorSettings } from '../../hooks/useEditorSettings'
import { useFullscreen } from '../../hooks/useFullscreen'
import { useMediaQuery } from '../../hooks/useMediaQuery'
import { useToast } from '../../hooks/useToast'
import { useApiQuery } from '../../hooks/useApiQuery'
import { executionService } from '../../services/executionService'
import { submissionService } from '../../services/submissionService'
import type { User } from '../../types/auth'
import type { Problem } from '../../types/problem'
import type { CustomTestCase, SupportedLanguage } from '../../types/workspace'
import { getErrorMessage } from '../../utils/errors'
import { cn } from '../../utils/format'
import { customTestStore, languagePreference } from '../../utils/workspaceStorage'
import { Alert } from '../ui/Alert'
import { Button } from '../ui/Button'
import { Modal } from '../ui/Modal'
import { editorModelPath, type CodeEditorApi } from './editorApi'
import { EditorToolbar } from './EditorToolbar'
import { EditorSkeleton, LazyCodeEditor } from './LazyCodeEditor'
import { ProblemPanel } from './ProblemPanel'
import { ResetCodeModal } from './ResetCodeModal'
import { SaveStatus } from './SaveStatus'
import { SplitPane } from './SplitPane'
import type { WorkspaceOutcome } from './results/outcome'
import { TestCasePanel, type PanelTab } from './TestCasePanel'
import { buildCases } from './testCases'
import { WorkspaceHeader } from './WorkspaceHeader'


function initialLanguage(userId: number, available: SupportedLanguage[]): SupportedLanguage {
  const preferred = languagePreference.get(userId)
  if (preferred && available.includes(preferred)) return preferred
  return available.includes(DEFAULT_LANGUAGE) ? DEFAULT_LANGUAGE : available[0]
}

export function CodingWorkspace({ problem, user }: { problem: Problem; user: User }) {
  const navigate = useNavigate()
  const { logout } = useAuth()
  const { toast } = useToast()
  const isDesktop = useMediaQuery('(min-width: 1024px)')
  const problemPath = `/student/problems/${problem.slug}`

  const [language, setLanguage] = useState<SupportedLanguage>(() => initialLanguage(user.id, problem.languages))
  const drafts = useDraftManager(user.id, problem, language)
  const { settings, update: updateSettings, reset: resetSettings } = useEditorSettings()
  const editorApi = useRef<CodeEditorApi | null>(null)
  const editorColumn = useRef<HTMLDivElement>(null)
  const fullscreen = useFullscreen(editorColumn)

  const [customCases, setCustomCases] = useState<CustomTestCase[]>(() => customTestStore.get(user.id, problem.id))
  const [selectedCaseId, setSelectedCaseId] = useState<string | null>(null)
  const [panelTab, setPanelTab] = useState<PanelTab>('tests')
  const [outcome, setOutcome] = useState<WorkspaceOutcome | null>(null)
  const [running, setRunning] = useState<'run' | 'submit' | null>(null)
  const runningRef = useRef(false)
  const [solved, setSolved] = useState(problem.user_status === 'SOLVED')
  // This problem's submission history (reloaded after each submission).
  const fetchHistory = useCallback(() => submissionService.list({ problem: problem.slug, limit: 10 }), [problem.slug])
  const history = useApiQuery(fetchHistory)
  const [resetOpen, setResetOpen] = useState(false)
  const [leaveTarget, setLeaveTarget] = useState<string | null>(null)
  const [loggingOut, setLoggingOut] = useState(false)
  const languageLabel = LANGUAGE_CONFIG[language].label

  useEffect(() => {
    document.title = `${problem.title} · Solve · CodeArena`
    return () => {
      document.title = 'CodeArena'
    }
  }, [problem.title])

  // ---------------------------------------------------------------- notifications
  const lastNotified = useRef<string | null>(null)
  useEffect(() => {
    const key = `${language}:${drafts.saveState}`
    if (lastNotified.current === key) return
    lastNotified.current = key
    if (drafts.saveState === 'error') toast('Draft could not be saved. Your code is kept in this browser.', { variant: 'error' })
    if (drafts.saveState === 'offline')
      toast('You appear to be offline. Your code is kept in this browser and will sync when the connection returns.', { variant: 'warning' })
  }, [drafts.saveState, language, toast])

  useEffect(() => {
    if (drafts.restoredFromBackup) toast('Restored unsaved changes from this browser.', { variant: 'info' })
  }, [drafts.restoredFromBackup, toast])

  // ---------------------------------------------------------------- leaving
  useEffect(() => {
    const onBeforeUnload = (event: BeforeUnloadEvent) => {
      if (!drafts.hasUnsavedChanges()) return
      drafts.backupAll()
      event.preventDefault()
      event.returnValue = ''
    }
    window.addEventListener('beforeunload', onBeforeUnload)
    return () => window.removeEventListener('beforeunload', onBeforeUnload)
  }, [drafts])

  const handleNavigate = useCallback(
    async (event: MouseEvent<HTMLAnchorElement>, to: string) => {
      if (!drafts.hasUnsavedChanges()) return // nothing pending: let the link navigate
      event.preventDefault()
      if (await drafts.flushAll()) navigate(to)
      else setLeaveTarget(to)
    },
    [drafts, navigate],
  )

  const handleLogout = async () => {
    setLoggingOut(true)
    drafts.backupAll()
    await drafts.flushAll()
    await logout()
    navigate('/login', { replace: true })
  }

  // ---------------------------------------------------------------- actions
  const changeLanguage = (next: SupportedLanguage) => {
    if (next === language) return
    languagePreference.set(user.id, next)
    setLanguage(next)
  }

  const confirmReset = async () => {
    setResetOpen(false)
    if (!editorApi.current) return
    editorApi.current.replaceAll(drafts.starterCode)
    await drafts.saveNow()
    toast(`${languageLabel} code reset to the starter code.`, { variant: 'success' })
  }

  const cases = buildCases(problem.sample_test_cases, customCases)
  const selectedCase = cases.find((c) => c.id === selectedCaseId) ?? cases[0] ?? null

  const execute = async (mode: 'run' | 'submit') => {
    if (runningRef.current) return // ignore double clicks while a request is in flight
    runningRef.current = true
    const sourceCode = editorApi.current?.getValue() ?? drafts.initialCode
    setRunning(mode)
    setPanelTab('result')
    try {
      if (mode === 'run') {
        const result = await executionService.runCode({
          problemId: problem.id,
          language,
          sourceCode,
          customCases: customCases.map((c) => ({ input: c.input, expected_output: c.expected.trim() ? c.expected : null })),
        })
        setOutcome({ mode, language, languageLabel, sourceCode, result })
        if (result.verdict === 'ACCEPTED') toast(`All ${result.total_tests} public tests passed. Submit to check the hidden tests.`, { variant: 'success' })
      } else {
        const submission = await executionService.submitCode({ problemId: problem.id, language, sourceCode })
        setOutcome({ mode, language, languageLabel, sourceCode, submission })
        history.reload()
        if (submission.status === 'ACCEPTED') {
          setSolved(true)
          toast(`Accepted! ${submission.passed_tests} / ${submission.total_tests} tests passed.`, { variant: 'success' })
        }
      }
    } catch (error) {
      // Network failure, rate limit (429), judge not configured (503)...: code and draft are untouched.
      toast(getErrorMessage(error), { variant: 'error' })
    } finally {
      runningRef.current = false
      setRunning(null)
    }
  }

  const updateCustomCases = (next: CustomTestCase[]) => {
    setCustomCases(next)
    customTestStore.set(user.id, problem.id, next)
  }

  const resolveConflict = async (choice: 'server' | 'mine') => {
    const code = await drafts.resolveConflict(choice)
    if (code !== null) editorApi.current?.replaceAll(code)
    toast(choice === 'mine' ? 'Your version was saved.' : 'Loaded the version saved in the other tab.', { variant: 'success' })
  }

  // ---------------------------------------------------------------- layout
  const banners = (
    <>
      {drafts.loadWarning && (
        <Alert variant="warning" className="m-2 mb-0 rounded-lg">
          {drafts.loadWarning}
        </Alert>
      )}
      {drafts.saveState === 'conflict' && (
        <Alert variant="warning" className="m-2 mb-0 rounded-lg">
          <p className="font-semibold">This draft was changed in another tab or window.</p>
          <p className="text-ink-500">Autosave is paused. Choose which version to keep:</p>
          <div className="mt-2 flex flex-wrap gap-2">
            <Button size="sm" variant="secondary" onClick={() => void resolveConflict('server')}>
              Load saved version
            </Button>
            <Button size="sm" onClick={() => void resolveConflict('mine')}>
              Keep my version
            </Button>
          </div>
        </Alert>
      )}
    </>
  )

  const editorArea = drafts.ready ? (
    <LazyCodeEditor
      path={editorModelPath(user.id, problem.id, language)}
      monacoLanguage={LANGUAGE_CONFIG[language].monacoId}
      defaultValue={drafts.initialCode}
      settings={settings}
      onChange={drafts.onEditorChange}
      onReady={(api) => {
        editorApi.current = api
      }}
      ariaLabel={`${languageLabel} code editor for ${problem.title}`}
    />
  ) : (
    <EditorSkeleton label="Loading your saved code" />
  )

  const editorColumnContent = (
    <div
      ref={editorColumn}
      className={cn(
        'flex min-h-0 flex-col bg-night',
        isDesktop ? 'h-full' : 'min-h-[640px]',
        fullscreen.fallbackActive && 'fixed inset-0 z-50 h-dvh',
      )}
    >
      {fullscreen.active && (
        <div className="flex items-center justify-between gap-2 border-b border-ink-200 bg-surface px-3 py-2">
          <p className="truncate text-sm font-bold text-ink-950">
            {problem.title} <span className="font-mono text-xs text-ink-500">· {languageLabel}</span>
          </p>
          <div className="flex items-center gap-3">
            <SaveStatus state={drafts.saveState} onRetry={drafts.retrySave} compact />
            <Button size="sm" variant="secondary" icon={<Minimize2 className="size-3.5" aria-hidden />} onClick={() => void fullscreen.exit()}>
              Exit fullscreen
            </Button>
          </div>
        </div>
      )}
      {banners}
      <div className={cn('min-h-0', isDesktop || fullscreen.active ? 'flex-1' : 'h-[60vh] min-h-[340px]')}>{editorArea}</div>
      <div className={cn('min-h-0 border-t border-ink-200', isDesktop || fullscreen.active ? 'h-[32%] min-h-44' : 'min-h-56')}>
        <TestCasePanel
          samples={problem.sample_test_cases}
          customCases={customCases}
          onAddCustom={(input, expected) => {
            const id = `custom-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`
            updateCustomCases([...customCases, { id, input, expected }])
            setSelectedCaseId(id)
          }}
          onRemoveCustom={(id) => {
            updateCustomCases(customCases.filter((c) => c.id !== id))
            setSelectedCaseId(null)
          }}
          selectedCaseId={selectedCase?.id ?? null}
          onSelectCase={setSelectedCaseId}
          tab={panelTab}
          onTabChange={setPanelTab}
          outcome={outcome}
          busy={running}
          onRetry={() => void execute(outcome?.mode ?? 'run')}
          submissions={{ items: history.data?.items ?? null, loading: history.loading, error: history.error }}
          problemSlug={problem.slug}
        />
      </div>
      <div className={cn(!isDesktop && !fullscreen.active && 'sticky bottom-0 z-10')}>
        <EditorToolbar
          onReset={() => setResetOpen(true)}
          onRun={() => void execute('run')}
          onSubmit={() => void execute('submit')}
          running={running}
          disabled={!drafts.ready}
        />
      </div>
    </div>
  )

  return (
    <div className={cn('flex flex-col bg-night', isDesktop ? 'h-dvh overflow-hidden' : 'min-h-dvh')}>
      <WorkspaceHeader
        user={user}
        problem={problem}
        problemPath={problemPath}
        language={language}
        onLanguageChange={changeLanguage}
        saveState={drafts.saveState}
        onRetrySave={drafts.retrySave}
        settings={settings}
        onSettingsChange={updateSettings}
        onSettingsReset={resetSettings}
        fullscreen={fullscreen.active}
        onToggleFullscreen={() => void fullscreen.toggle()}
        onNavigate={(event, to) => void handleNavigate(event, to)}
        onLogout={() => void handleLogout()}
        loggingOut={loggingOut}
      />
      {isDesktop ? (
        <main className="min-h-0 flex-1">
          <SplitPane left={<ProblemPanel problem={problem} solved={solved} />} right={editorColumnContent} />
        </main>
      ) : (
        <main className="flex flex-col">
          <div className="max-h-[70vh] overflow-y-auto border-b border-ink-200">
            <ProblemPanel problem={problem} solved={solved} />
          </div>
          {editorColumnContent}
        </main>
      )}

      <ResetCodeModal open={resetOpen} languageLabel={languageLabel} onCancel={() => setResetOpen(false)} onConfirm={() => void confirmReset()} />
      <Modal
        open={leaveTarget !== null}
        onClose={() => setLeaveTarget(null)}
        title="Leave without saving?"
        description="Your latest changes could not be saved to the server. They are kept in this browser and will be restored when you come back."
        footer={
          <>
            <Button variant="secondary" onClick={() => setLeaveTarget(null)}>
              Stay
            </Button>
            <Button
              variant="danger"
              onClick={() => {
                drafts.backupAll()
                const target = leaveTarget
                setLeaveTarget(null)
                if (target) navigate(target)
              }}
            >
              Leave
            </Button>
          </>
        }
      >
        <p className="text-sm text-ink-500">Check your connection and try again to save to your account.</p>
      </Modal>
    </div>
  )
}
