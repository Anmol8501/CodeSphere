import Editor from '@monaco-editor/react'
import { useEffect } from 'react'
import { monaco } from '../workspace/monaco/monacoSetup'

export interface CodeViewerProps {
  code: string
  monacoLanguage: string
  /** Model URI, unique per submission (never shared with the editable workspace models). */
  path: string
  ariaLabel: string
  height: number
}

/** Read-only Monaco view of submitted code. Lazy-loaded (pulls in the Monaco bundle). */
export default function CodeViewer({ code, monacoLanguage, path, ariaLabel, height }: CodeViewerProps) {
  // Dispose the read-only model when leaving so submitted code never lingers in memory.
  useEffect(
    () => () => {
      window.setTimeout(() => {
        const model = monaco.editor.getModel(monaco.Uri.parse(path))
        if (model && !model.isDisposed() && !model.isAttachedToEditor()) model.dispose()
      }, 0)
    },
    [path],
  )

  return (
    <Editor
      path={path}
      language={monacoLanguage}
      value={code}
      theme="codearena-dark"
      height={height}
      options={{
        readOnly: true,
        domReadOnly: true,
        readOnlyMessage: { value: 'Submitted code cannot be edited. Use "Open in editor" to keep working.' },
        fontSize: 13,
        fontFamily: '"JetBrains Mono", ui-monospace, SFMono-Regular, Menlo, Consolas, monospace',
        minimap: { enabled: false },
        lineNumbers: 'on',
        wordWrap: 'on',
        scrollBeyondLastLine: false,
        automaticLayout: true,
        renderLineHighlight: 'none',
        contextmenu: false,
        padding: { top: 12, bottom: 12 },
        ariaLabel,
      }}
    />
  )
}
