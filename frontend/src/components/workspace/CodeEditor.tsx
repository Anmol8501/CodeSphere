import Editor, { type OnMount } from '@monaco-editor/react'
import { useEffect, useMemo, useRef } from 'react'
import type { EditorSettings } from '../../types/workspace'
import type { CodeEditorApi } from './editorApi'
import { MODEL_AUTHORITY } from './editorApi'
import { monaco } from './monaco/monacoSetup'

export interface CodeEditorProps {
  /** Model URI: one model (and undo history) per user/problem/language. */
  path: string
  monacoLanguage: string
  /** Used only when the model for `path` is first created. */
  defaultValue: string
  settings: EditorSettings
  onChange: (value: string) => void
  onReady: (api: CodeEditorApi) => void
  ariaLabel: string
}

function EditorLoading() {
  return (
    <div className="flex h-full items-center justify-center bg-[#070b07]" role="status" aria-label="Loading code editor">
      <span className="font-mono text-xs tracking-wider text-ink-400 uppercase">Loading editor...</span>
    </div>
  )
}

/** Monaco wrapper. Lazy-loaded: importing this file pulls in the Monaco bundle. */
export default function CodeEditor({
  path,
  monacoLanguage,
  defaultValue,
  settings,
  onChange,
  onReady,
  ariaLabel,
}: CodeEditorProps) {
  const onChangeRef = useRef(onChange)
  useEffect(() => {
    onChangeRef.current = onChange
  }, [onChange])

  // Rebuilt only when a setting changes, never on keystrokes.
  const options = useMemo(
    () => ({
      fontSize: settings.fontSize,
      fontFamily: '"JetBrains Mono", ui-monospace, SFMono-Regular, Menlo, Consolas, monospace',
      tabSize: settings.tabSize,
      insertSpaces: true,
      detectIndentation: false,
      wordWrap: settings.wordWrap ? ('on' as const) : ('off' as const),
      minimap: { enabled: settings.minimap },
      lineNumbers: 'on' as const,
      automaticLayout: true,
      scrollBeyondLastLine: false,
      matchBrackets: 'always' as const,
      bracketPairColorization: { enabled: true },
      guides: { bracketPairs: true, indentation: true },
      quickSuggestions: true,
      suggestOnTriggerCharacters: true,
      smoothScrolling: true,
      cursorBlinking: 'smooth' as const,
      renderLineHighlight: 'all' as const,
      padding: { top: 12, bottom: 12 },
      ariaLabel,
      accessibilitySupport: 'auto' as const,
    }),
    [settings.fontSize, settings.tabSize, settings.wordWrap, settings.minimap, ariaLabel],
  )

  const handleMount: OnMount = (editor) => {
    onReady({
      replaceAll: (code) => {
        const model = editor.getModel()
        if (!model) return
        editor.pushUndoStop()
        editor.executeEdits('codearena', [{ range: model.getFullModelRange(), text: code }])
        editor.pushUndoStop()
      },
      getValue: () => editor.getValue(),
      focus: () => editor.focus(),
    })
  }

  // Leaving the workspace disposes this user's in-memory models so code never
  // lingers for the next person using this browser tab. Deferred so the
  // wrapper disposes its editor first; models a live editor uses are kept.
  useEffect(
    () => () => {
      window.setTimeout(() => {
        monaco.editor
          .getModels()
          .filter((model) => model.uri.authority === MODEL_AUTHORITY && !model.isDisposed() && !model.isAttachedToEditor())
          .forEach((model) => model.dispose())
      }, 0)
    },
    [],
  )

  return (
    <Editor
      path={path}
      language={monacoLanguage}
      defaultValue={defaultValue}
      theme={settings.theme}
      options={options}
      onMount={handleMount}
      onChange={(value) => onChangeRef.current(value ?? '')}
      loading={<EditorLoading />}
      saveViewState
    />
  )
}
