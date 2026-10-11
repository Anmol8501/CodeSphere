import { AlertOctagon, RefreshCw } from 'lucide-react'
import { Component, useEffect, useState, type ComponentType, type ReactNode } from 'react'
import { Button } from '../ui/Button'
import type { CodeEditorProps } from './CodeEditor'

class EditorErrorBoundary extends Component<{ children: ReactNode; fallback: ReactNode }, { failed: boolean }> {
  state = { failed: false }

  static getDerivedStateFromError() {
    return { failed: true }
  }

  render() {
    return this.state.failed ? this.props.fallback : this.props.children
  }
}

export function EditorSkeleton({ label = 'Loading code editor' }: { label?: string }) {
  return (
    <div className="h-full space-y-2.5 bg-[#070b07] p-5" role="status" aria-label={label}>
      <span className="sr-only">{label}</span>
      {[40, 64, 52, 72, 30, 58, 44].map((width, i) => (
        <div key={i} className="flex items-center gap-4">
          <div className="h-3 w-5 animate-shimmer rounded bg-ink-100" aria-hidden />
          <div className="h-3 animate-shimmer rounded bg-ink-100" style={{ width: `${width}%` }} aria-hidden />
        </div>
      ))}
    </div>
  )
}

type LoadState = { status: 'loading' } | { status: 'ready'; Editor: ComponentType<CodeEditorProps> } | { status: 'failed' }

/**
 * Loads the Monaco chunk on demand. If the chunk (or Monaco itself) fails,
 * the workspace stays usable: the problem panel remains and the student can
 * retry, instead of getting a blank page.
 */
export function LazyCodeEditor(props: CodeEditorProps) {
  const [attempt, setAttempt] = useState(0)
  const [load, setLoad] = useState<LoadState>({ status: 'loading' })

  useEffect(() => {
    let cancelled = false
    import('./CodeEditor')
      .then((module) => !cancelled && setLoad({ status: 'ready', Editor: module.default }))
      .catch(() => !cancelled && setLoad({ status: 'failed' }))
    return () => {
      cancelled = true
    }
  }, [attempt])

  const retry = () => {
    setLoad({ status: 'loading' })
    // Browsers may cache a failed dynamic import, so a second failure falls
    // back to reloading the page. Nothing is lost: the editor never loaded,
    // and saved drafts come back from the server.
    import('./CodeEditor')
      .then(() => setAttempt((n) => n + 1))
      .catch(() => window.location.reload())
  }

  const fallback = (
    <div className="flex h-full flex-col items-center justify-center gap-3 bg-[#070b07] p-6 text-center" role="alert">
      <span className="flex size-11 items-center justify-center rounded-xl bg-danger/10 text-danger ring-1 ring-danger/25">
        <AlertOctagon className="size-5" aria-hidden />
      </span>
      <p className="font-semibold text-ink-950">Code editor could not be loaded.</p>
      <p className="max-w-xs text-sm text-ink-500">Check your connection. The problem statement is still available.</p>
      <Button variant="secondary" size="sm" icon={<RefreshCw className="size-3.5" aria-hidden />} onClick={retry}>
        Retry
      </Button>
    </div>
  )

  if (load.status === 'failed') return fallback
  if (load.status === 'loading') return <EditorSkeleton />
  const { Editor } = load
  return (
    <EditorErrorBoundary key={attempt} fallback={fallback}>
      <Editor {...props} />
    </EditorErrorBoundary>
  )
}
