import { Settings2 } from 'lucide-react'
import type { EditorSettings, EditorThemeName } from '../../types/workspace'
import { Dropdown } from '../ui/Dropdown'
import { Select } from '../ui/Select'
import { Switch } from '../ui/Switch'

const FONT_SIZES = [12, 13, 14, 15, 16, 18, 20, 22, 24]
const THEMES: { value: EditorThemeName; label: string }[] = [
  { value: 'codearena-dark', label: 'CodeArena Dark' },
  { value: 'vs-dark', label: 'VS Dark' },
  { value: 'hc-black', label: 'High Contrast' },
]

interface EditorSettingsMenuProps {
  settings: EditorSettings
  onChange: (patch: Partial<EditorSettings>) => void
  onReset: () => void
}

/** Editor preferences (saved in this browser). */
export function EditorSettingsMenu({ settings, onChange, onReset }: EditorSettingsMenuProps) {
  return (
    <Dropdown
      role="dialog"
      label="Editor settings"
      widthClass="w-72"
      trigger={(props) => (
        <button
          type="button"
          {...props}
          aria-label="Editor settings"
          title="Editor settings"
          className="flex size-9 items-center justify-center rounded-lg text-ink-500 ring-1 ring-ink-200 transition hover:text-ink-950 hover:ring-brand-500/40"
        >
          <Settings2 className="size-4" aria-hidden />
        </button>
      )}
    >
      {() => (
        <div className="space-y-4 p-4">
          <p className="font-mono text-[11px] font-semibold tracking-[0.14em] text-ink-950 uppercase">Editor settings</p>
          <div className="grid grid-cols-2 gap-3">
            <Select
              label="Font size"
              value={String(settings.fontSize)}
              onChange={(v) => onChange({ fontSize: Number(v) })}
              options={FONT_SIZES.map((size) => ({ value: String(size), label: `${size}px` }))}
            />
            <Select
              label="Tab size"
              value={String(settings.tabSize)}
              onChange={(v) => onChange({ tabSize: Number(v) as EditorSettings['tabSize'] })}
              options={[2, 4, 8].map((size) => ({ value: String(size), label: `${size} spaces` }))}
            />
          </div>
          <Select<EditorThemeName> label="Theme" value={settings.theme} onChange={(theme) => onChange({ theme })} options={THEMES} />
          <Switch label="Word wrap" checked={settings.wordWrap} onChange={(wordWrap) => onChange({ wordWrap })} />
          <Switch label="Minimap" checked={settings.minimap} onChange={(minimap) => onChange({ minimap })} />
          <button type="button" onClick={onReset} className="text-xs font-semibold text-ink-500 underline-offset-2 hover:text-ink-950 hover:underline">
            Restore defaults
          </button>
        </div>
      )}
    </Dropdown>
  )
}
