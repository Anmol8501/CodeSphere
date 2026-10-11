import { Check, Plus } from 'lucide-react'
import { useState, type FormEvent } from 'react'
import { adminProblemService } from '../../../services/adminProblemService'
import type { Tag } from '../../../types/problem'
import { getErrorMessage } from '../../../utils/errors'
import { cn } from '../../../utils/format'
import { Button } from '../../ui/Button'

interface TagPickerProps {
  tags: Tag[]
  selected: number[]
  onChange: (ids: number[]) => void
  /** Called after a new tag is created so the parent can add it to `tags`. */
  onTagCreated: (tag: Tag) => void
}

const MAX_TAGS = 10

export function TagPicker({ tags, selected, onChange, onTagCreated }: TagPickerProps) {
  const [newTag, setNewTag] = useState('')
  const [creating, setCreating] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const toggle = (id: number) => {
    if (selected.includes(id)) onChange(selected.filter((t) => t !== id))
    else if (selected.length < MAX_TAGS) onChange([...selected, id])
  }

  const create = async (event?: FormEvent) => {
    event?.preventDefault()
    const name = newTag.trim()
    if (!name) return
    setCreating(true)
    setError(null)
    try {
      const tag = await adminProblemService.createTag(name)
      onTagCreated(tag)
      if (selected.length < MAX_TAGS) onChange([...selected, tag.id])
      setNewTag('')
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setCreating(false)
    }
  }

  return (
    <fieldset>
      <legend className="mb-1.5 text-sm font-semibold text-ink-800">
        Tags <span className="font-normal text-ink-400">({selected.length}/{MAX_TAGS})</span>
      </legend>
      <div className="flex flex-wrap gap-1.5">
        {tags.map((tag) => {
          const active = selected.includes(tag.id)
          return (
            <button
              key={tag.id}
              type="button"
              aria-pressed={active}
              onClick={() => toggle(tag.id)}
              className={cn(
                'inline-flex items-center gap-1 rounded-md border px-2 py-1 font-mono text-[11px] font-semibold tracking-wider uppercase transition',
                active
                  ? 'border-brand-500/50 bg-brand-500/10 text-brand-400'
                  : 'border-ink-200 bg-night text-ink-500 hover:border-brand-500/30 hover:text-ink-900',
              )}
            >
              {active && <Check className="size-3" aria-hidden />}
              {tag.name}
            </button>
          )
        })}
        {tags.length === 0 && <p className="text-sm text-ink-500">No tags yet. Create the first one below.</p>}
      </div>

      <div className="mt-3 flex max-w-sm gap-2">
        <input
          value={newTag}
          onChange={(event) => setNewTag(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === 'Enter') void create(event)
          }}
          placeholder="New tag name"
          aria-label="New tag name"
          maxLength={50}
          className="h-8 min-w-0 flex-1 rounded-lg border border-ink-200 bg-night px-3 text-sm text-ink-950 placeholder:text-ink-400 focus:border-brand-500 focus:ring-4 focus:ring-brand-500/15 focus:outline-none"
        />
        <Button size="sm" variant="secondary" icon={<Plus className="size-3.5" aria-hidden />} loading={creating} onClick={() => void create()}>
          Add tag
        </Button>
      </div>
      {error && <p className="mt-1.5 text-[13px] text-danger">{error}</p>}
    </fieldset>
  )
}
