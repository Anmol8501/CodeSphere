import { LANGUAGE_CONFIG } from '../../config/languages'
import type { SupportedLanguage } from '../../types/workspace'
import { Select } from '../ui/Select'

interface LanguageSelectorProps {
  /** Languages this problem offers (from the backend). */
  languages: SupportedLanguage[]
  value: SupportedLanguage
  onChange: (language: SupportedLanguage) => void
  disabled?: boolean
  className?: string
}

/** Native <select> for full keyboard and screen-reader support. */
export function LanguageSelector({ languages, value, onChange, disabled, className }: LanguageSelectorProps) {
  return (
    <Select<SupportedLanguage>
      label="Language"
      hideLabel
      className={className}
      value={value}
      disabled={disabled}
      onChange={onChange}
      options={languages.map((lang) => ({ value: lang, label: LANGUAGE_CONFIG[lang].label }))}
    />
  )
}
