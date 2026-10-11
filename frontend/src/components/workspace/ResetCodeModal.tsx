import { Button } from '../ui/Button'
import { Modal } from '../ui/Modal'

interface ResetCodeModalProps {
  open: boolean
  languageLabel: string
  onCancel: () => void
  onConfirm: () => void
}

export function ResetCodeModal({ open, languageLabel, onCancel, onConfirm }: ResetCodeModalProps) {
  return (
    <Modal
      open={open}
      onClose={onCancel}
      title="Reset code?"
      description={`Your current ${languageLabel} code for this problem will be replaced with the original starter code.`}
      footer={
        <>
          <Button variant="secondary" onClick={onCancel}>
            Cancel
          </Button>
          <Button variant="danger" onClick={onConfirm}>
            Reset
          </Button>
        </>
      }
    >
      <p className="text-sm text-ink-500">
        You can still undo the reset in the editor with <kbd className="rounded bg-night px-1 font-mono text-xs ring-1 ring-ink-200">Ctrl</kbd>+
        <kbd className="rounded bg-night px-1 font-mono text-xs ring-1 ring-ink-200">Z</kbd> before leaving the page.
      </p>
    </Modal>
  )
}
