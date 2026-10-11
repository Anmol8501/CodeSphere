import { ChevronDown } from 'lucide-react'
import { useState, type KeyboardEvent } from 'react'
import type { Language } from '../../../types/problem'
import { LANGUAGE_LABEL } from '../../problems/labels'
import { Tabs } from '../../ui/Tabs'
import { TextArea } from '../../ui/TextArea'
import { LANGUAGES, USER_CODE_MARKER } from './formState'

interface StarterCodeEditorProps {
  value: Record<Language, string>
  onChange: (value: Record<Language, string>) => void
  drivers: Record<Language, string>
  onDriversChange: (value: Record<Language, string>) => void
  driverError?: string
}

/** Insert spaces instead of moving focus when Tab is pressed in a code box. */
function tabInserter(update: (next: string) => void) {
  return (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key !== 'Tab' || event.shiftKey) return
    event.preventDefault()
    const target = event.currentTarget
    const { selectionStart, selectionEnd } = target
    update(`${target.value.slice(0, selectionStart)}    ${target.value.slice(selectionEnd)}`)
    requestAnimationFrame(() => target.setSelectionRange(selectionStart + 4, selectionStart + 4))
  }
}

/**
 * Starter code (shown to students) and the optional hidden execution harness
 * per language. Leave a language's starter empty to not offer that language.
 */
export function StarterCodeEditor({ value, onChange, drivers, onDriversChange, driverError }: StarterCodeEditorProps) {
  const [language, setLanguage] = useState<Language>('CPP')
  return (
    <div>
      <Tabs<Language>
        ariaLabel="Starter code language"
        size="sm"
        value={language}
        onChange={setLanguage}
        options={LANGUAGES.map((lang) => ({
          value: lang,
          label: `${LANGUAGE_LABEL[lang]}${value[lang].trim() ? '' : ' (empty)'}`,
        }))}
      />
      <TextArea
        className="mt-3"
        label={`${LANGUAGE_LABEL[language]} starter code`}
        mono
        rows={10}
        maxLength={20000}
        value={value[language]}
        onChange={(event) => onChange({ ...value, [language]: event.target.value })}
        onKeyDown={tabInserter((next) => onChange({ ...value, [language]: next }))}
        hint="What students see when they open the editor. Leave empty to not offer this language."
      />
      <details className="group mt-4 rounded-xl border border-ink-200 bg-night/40" open={Boolean(drivers[language].trim()) || Boolean(driverError)}>
        <summary className="flex cursor-pointer list-none items-center justify-between gap-2 px-4 py-2.5 text-sm font-semibold text-ink-800 [&::-webkit-details-marker]:hidden">
          Hidden execution harness ({LANGUAGE_LABEL[language]}, advanced)
          <ChevronDown className="size-4 text-ink-400 transition group-open:rotate-180" aria-hidden />
        </summary>
        <div className="px-4 pb-4">
          <TextArea
            label={`${LANGUAGE_LABEL[language]} execution harness`}
            mono
            rows={10}
            maxLength={50000}
            value={drivers[language]}
            error={driverError}
            onChange={(event) => onDriversChange({ ...drivers, [language]: event.target.value })}
            onKeyDown={tabInserter((next) => onDriversChange({ ...drivers, [language]: next }))}
            hint={`For "implement this function" problems: a full program containing ${USER_CODE_MARKER} on its own line. The student's code is inserted there; the harness reads the input, calls the function and prints the result. Never shown to students. Leave empty if students write the whole program.`}
          />
        </div>
      </details>
    </div>
  )
}
