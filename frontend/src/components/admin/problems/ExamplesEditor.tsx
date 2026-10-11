import { Plus, Trash2 } from 'lucide-react'
import { Button } from '../../ui/Button'
import { TextArea } from '../../ui/TextArea'
import { emptyExample, type ExampleDraft } from './formState'

interface ExamplesEditorProps {
  examples: ExampleDraft[]
  onChange: (examples: ExampleDraft[]) => void
  error?: string
}

const MAX_EXAMPLES = 10

/** Public worked examples shown in the problem statement. */
export function ExamplesEditor({ examples, onChange, error }: ExamplesEditorProps) {
  const update = (key: string, patch: Partial<ExampleDraft>) =>
    onChange(examples.map((e) => (e.key === key ? { ...e, ...patch } : e)))

  return (
    <div className="space-y-4">
      {examples.map((example, index) => (
        <div key={example.key} role="group" aria-label={`Example ${index + 1}`} className="rounded-xl border border-ink-200 bg-night/40 p-4">
          <div className="mb-3 flex items-center justify-between gap-2">
            <p className="text-sm font-semibold text-ink-950">Example {index + 1}</p>
            <Button
              size="sm"
              variant="ghost"
              icon={<Trash2 className="size-3.5" aria-hidden />}
              aria-label={`Remove example ${index + 1}`}
              onClick={() => onChange(examples.filter((e) => e.key !== example.key))}
            >
              Remove
            </Button>
          </div>
          <div className="grid gap-3 md:grid-cols-2">
            <TextArea label={`Example ${index + 1} input`} mono rows={3} value={example.input} maxLength={5000}
              onChange={(event) => update(example.key, { input: event.target.value })} />
            <TextArea label={`Example ${index + 1} output`} mono rows={3} value={example.output} maxLength={5000}
              onChange={(event) => update(example.key, { output: event.target.value })} />
          </div>
          <TextArea className="mt-3" label={`Example ${index + 1} explanation (optional)`} rows={2} value={example.explanation} maxLength={2000}
            onChange={(event) => update(example.key, { explanation: event.target.value })} />
        </div>
      ))}
      {examples.length === 0 && <p className="text-sm text-ink-500">No examples yet.</p>}
      {error && <p className="text-[13px] text-danger" role="alert">{error}</p>}
      <Button
        size="sm"
        variant="secondary"
        icon={<Plus className="size-3.5" aria-hidden />}
        disabled={examples.length >= MAX_EXAMPLES}
        onClick={() => onChange([...examples, emptyExample()])}
      >
        Add example
      </Button>
    </div>
  )
}
