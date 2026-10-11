import type * as Monaco from 'monaco-editor/editor/editor.api'

/**
 * CodeArena editor theme: near-black surface, readable neutral text, and
 * green only for the cursor, active line number, selection and accents.
 */
export function registerThemes(monaco: typeof Monaco): void {
  monaco.editor.defineTheme('codearena-dark', {
    base: 'vs-dark',
    inherit: true,
    rules: [
      { token: '', foreground: 'dfe6df' },
      { token: 'comment', foreground: '667466', fontStyle: 'italic' },
      { token: 'keyword', foreground: '7ee08f' },
      { token: 'string', foreground: 'e5c07b' },
      { token: 'number', foreground: '79c0ff' },
      { token: 'type', foreground: '5fd4d4' },
      { token: 'type.identifier', foreground: '5fd4d4' },
      { token: 'delimiter', foreground: 'a5ada5' },
      { token: 'operator', foreground: 'c3cbc3' },
      { token: 'annotation', foreground: 'd2a8ff' },
    ],
    colors: {
      'editor.background': '#070b07',
      'editor.foreground': '#dfe6df',
      'editorCursor.foreground': '#39ff14',
      'editor.lineHighlightBackground': '#0e150e',
      'editor.lineHighlightBorder': '#00000000',
      'editorLineNumber.foreground': '#3c4a3c',
      'editorLineNumber.activeForeground': '#8dff74',
      'editor.selectionBackground': '#39ff142e',
      'editor.inactiveSelectionBackground': '#39ff1414',
      'editor.selectionHighlightBackground': '#39ff1414',
      'editor.findMatchBackground': '#f5c54255',
      'editor.findMatchHighlightBackground': '#f5c54222',
      'editorBracketMatch.background': '#39ff1414',
      'editorBracketMatch.border': '#39ff1466',
      'editorIndentGuide.background1': '#1b261b',
      'editorIndentGuide.activeBackground1': '#2f4a2f',
      'editorWhitespace.foreground': '#1f2b1f',
      'editorWidget.background': '#0b100b',
      'editorWidget.border': '#1b261b',
      'editorSuggestWidget.background': '#0b100b',
      'editorSuggestWidget.border': '#1b261b',
      'editorSuggestWidget.selectedBackground': '#13251a',
      'editorHoverWidget.background': '#0b100b',
      'editorHoverWidget.border': '#1b261b',
      focusBorder: '#39ff1466',
      'scrollbarSlider.background': '#2a382a80',
      'scrollbarSlider.hoverBackground': '#3c4f3ccc',
      'minimap.background': '#070b07',
    },
  })
}
