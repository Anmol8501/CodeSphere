/**
 * Bundles Monaco locally (no CDN) with only the features and languages
 * CodeArena needs, and points @monaco-editor/react at this instance.
 * Imported only by the code editor chunk, so Monaco downloads only when the
 * coding workspace opens.
 */
import { loader } from '@monaco-editor/react'
import * as monaco from 'monaco-editor/editor/editor.api'
import EditorWorker from 'monaco-editor/editor/editor.worker?worker'
import './monacoFeatures.js'
import { registerThemes } from './themes'

interface MonacoWindow {
  MonacoEnvironment?: { getWorker: (workerId: string, label: string) => Worker }
}

// The plain editor worker is all that C++/Java/Python syntax support needs.
const monacoWindow = self as unknown as MonacoWindow
monacoWindow.MonacoEnvironment = { getWorker: () => new EditorWorker() }

registerThemes(monaco)
loader.config({ monaco })

export { monaco }
