// Shared, Monaco-free pieces of the editor contract. Kept separate from
// CodeEditor.tsx so importing them never pulls the Monaco bundle.

/** Imperative handle the workspace uses for reset / conflict resolution. */
export interface CodeEditorApi {
  /** Replace the whole document as one undoable edit (fires onChange). */
  replaceAll: (code: string) => void
  getValue: () => string
  focus: () => void
}

export const MODEL_AUTHORITY = 'codearena'

export function editorModelPath(userId: number, problemId: number, language: string): string {
  return `inmemory://${MODEL_AUTHORITY}/${userId}/${problemId}/${language}`
}
