import { Play, RotateCcw, Send } from 'lucide-react'
import { Button } from '../ui/Button'

interface EditorToolbarProps {
  onReset: () => void
  onRun: () => void
  onSubmit: () => void
  running: 'run' | 'submit' | null
  disabled?: boolean
}

/** Reset / Run / Submit. Run and Submit go through executionService; both lock while one is in flight. */
export function EditorToolbar({ onReset, onRun, onSubmit, running, disabled }: EditorToolbarProps) {
  return (
    <div className="flex items-center justify-between gap-2 border-t border-ink-200 bg-surface px-3 py-2.5">
      <Button size="sm" variant="ghost" icon={<RotateCcw className="size-3.5" aria-hidden />} onClick={onReset} disabled={disabled}>
        Reset Code
      </Button>
      <div className="flex gap-2">
        <Button
          size="sm"
          variant="secondary"
          icon={<Play className="size-3.5" aria-hidden />}
          onClick={onRun}
          loading={running === 'run'}
          loadingText="Running..."
          disabled={disabled || running !== null}
        >
          Run
        </Button>
        <Button
          size="sm"
          icon={<Send className="size-3.5" aria-hidden />}
          onClick={onSubmit}
          loading={running === 'submit'}
          loadingText="Submitting..."
          disabled={disabled || running !== null}
        >
          Submit
        </Button>
      </div>
    </div>
  )
}
