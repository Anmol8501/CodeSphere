import { useEffect, useState, type ComponentType } from 'react'
import { LANGUAGE_CONFIG } from '../../config/languages'
import type { Language } from '../../types/problem'
import { EditorSkeleton } from '../workspace/LazyCodeEditor'
import type { CodeViewerProps } from './CodeViewer'

interface LazyCodeViewerProps {
  code: string
  language: Language
  /** Unique id for the read-only model, e.g. "submission-42". */
  modelId: string
  ariaLabel?: string
  maxHeight?: number
}

type LoadState = { status: 'loading' } | { status: 'ready'; Viewer: ComponentType<CodeViewerProps> } | { status: 'failed' }

/**
 * Syntax-highlighted, read-only code. Loads Monaco on demand; if it cannot
 * load, the code is still shown as plain text (never a blank area).
 */
export function LazyCodeViewer({ code, language, modelId, ariaLabel, maxHeight = 560 }: LazyCodeViewerProps) {
  const [load, setLoad] = useState<LoadState>({ status: 'loading' })
  useEffect(() => {
    let cancelled = false
    import('./CodeViewer')
      .then((module) => !cancelled && setLoad({ status: 'ready', Viewer: module.default }))
      .catch(() => !cancelled && setLoad({ status: 'failed' }))
    return () => {
      cancelled = true
    }
  }, [])

  const lines = code.split('\n').length
  const height = Math.min(Math.max(lines * 19 + 24, 120), maxHeight)
  const label = ariaLabel ?? `${LANGUAGE_CONFIG[language].label} code (read-only)`

  if (load.status === 'failed') {
    return (
      <pre
        aria-label={label}
        className="overflow-auto rounded-lg bg-[#070b07] p-4 font-mono text-[13px] leading-relaxed text-ink-900 ring-1 ring-ink-200"
        style={{ maxHeight }}
      >
        {code}
      </pre>
    )
  }
  return (
    <div className="overflow-hidden rounded-lg ring-1 ring-ink-200" style={{ height }}>
      {load.status === 'loading' ? (
        <EditorSkeleton label="Loading code" />
      ) : (
        <load.Viewer
          code={code}
          monacoLanguage={LANGUAGE_CONFIG[language].monacoId}
          path={`inmemory://codearena-view/${modelId}`}
          ariaLabel={label}
          height={height}
        />
      )}
    </div>
  )
}
