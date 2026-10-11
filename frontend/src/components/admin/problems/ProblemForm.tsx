import { Code2, FileText, FlaskConical, Gauge, ListChecks, Plus, Rocket, Save, Settings2, Trash2 } from 'lucide-react'
import { useState, type FormEvent } from 'react'
import { useApiQuery } from '../../../hooks/useApiQuery'
import { problemService } from '../../../services/problemService'
import type { Difficulty, Tag, Topic } from '../../../types/problem'
import { getErrorMessage, getFieldErrors } from '../../../utils/errors'
import { Alert } from '../../ui/Alert'
import { Button, ButtonLink } from '../../ui/Button'
import { SectionCard } from '../../ui/Card'
import { Select } from '../../ui/Select'
import { Switch } from '../../ui/Switch'
import { TextArea } from '../../ui/TextArea'
import { TextField } from '../../ui/TextField'
import { ExamplesEditor } from './ExamplesEditor'
import { emptyTestCase, slugify, validate, type FormErrors, type ProblemFormValues } from './formState'
import { StarterCodeEditor } from './StarterCodeEditor'
import { TagPicker } from './TagPicker'
import { TestCaseFields } from './TestCaseFields'

const DIFFICULTY_OPTIONS: { value: Difficulty; label: string }[] = [
  { value: 'EASY', label: 'Easy' },
  { value: 'MEDIUM', label: 'Medium' },
  { value: 'HARD', label: 'Hard' },
]

// Server field paths ("title", "examples.0.input", ...) -> form error keys.
function mapServerErrors(error: unknown): FormErrors {
  const result: FormErrors = {}
  for (const [field, message] of Object.entries(getFieldErrors(error))) {
    if (field === 'title' || field === 'slug' || field === 'description') result[field] = message
    else if (field === 'topic_id') result.topicId = message
    else if (field.startsWith('examples')) result.examples = message
    else if (field.startsWith('test_cases')) result.testCases = message
    else if (field === 'time_limit_ms' || field === 'memory_limit_kb') result.limits = message
    else if (field.includes('driver_code')) result.drivers = message
  }
  return result
}

interface ProblemFormProps {
  mode: 'create' | 'edit'
  initialValues: ProblemFormValues
  topics: Topic[]
  /** Throws on failure; the form shows the error. */
  onSubmit: (values: ProblemFormValues) => Promise<void>
  /** Edit mode: link to the test case manager. */
  testCasesLink?: { to: string; count: number; hidden: number }
}

export function ProblemForm({ mode, initialValues, topics, onSubmit, testCasesLink }: ProblemFormProps) {
  const [values, setValues] = useState(initialValues)
  const [errors, setErrors] = useState<FormErrors>({})
  const [submitError, setSubmitError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const tagQuery = useApiQuery(problemService.listTags)
  const [createdTags, setCreatedTags] = useState<Tag[]>([])
  const tags = [...(tagQuery.data ?? []), ...createdTags.filter((t) => !tagQuery.data?.some((d) => d.id === t.id))].sort((a, b) =>
    a.name.localeCompare(b.name),
  )

  const set = <K extends keyof ProblemFormValues>(key: K, value: ProblemFormValues[K]) =>
    setValues((current) => ({ ...current, [key]: value }))

  const onTitleChange = (title: string) =>
    setValues((current) => ({ ...current, title, slug: current.slugTouched ? current.slug : slugify(title) }))

  const submit = async (event: FormEvent) => {
    event.preventDefault()
    const found = validate(values, mode)
    setErrors(found)
    setSubmitError(null)
    if (Object.keys(found).length > 0) {
      setSubmitError('Please fix the highlighted fields.')
      return
    }
    setSubmitting(true)
    try {
      await onSubmit(values)
    } catch (err) {
      setErrors(mapServerErrors(err))
      setSubmitError(getErrorMessage(err))
      setSubmitting(false)
    }
  }

  const topicOptions = [
    { value: '', label: 'Select a topic' },
    ...topics.map((t) => ({ value: String(t.id), label: `${String(t.order_index).padStart(2, '0')} · ${t.name}` })),
  ]

  return (
    <form onSubmit={submit} noValidate className="space-y-6">
      {submitError && <Alert variant="error">{submitError}</Alert>}

      <SectionCard title="Basics" description="Title, difficulty, topic and tags" icon={<Settings2 />}>
        <div className="grid gap-4 md:grid-cols-2">
          <TextField label="Title" value={values.title} error={errors.title} maxLength={150} required
            onChange={(event) => onTitleChange(event.target.value)} placeholder="e.g. Two Sum" />
          <TextField label="Slug" value={values.slug} error={errors.slug} maxLength={160}
            onChange={(event) => setValues((c) => ({ ...c, slug: event.target.value.toLowerCase(), slugTouched: true }))}
            hint={values.slug ? `URL: /student/problems/${values.slug}` : 'Generated from the title.'} />
          <Select label="Difficulty" value={values.difficulty} options={DIFFICULTY_OPTIONS} onChange={(v) => set('difficulty', v)} />
          <div>
            <Select label="Topic" value={values.topicId} options={topicOptions} onChange={(v) => set('topicId', v)} />
            {errors.topicId && <p className="mt-1.5 text-[13px] text-danger">{errors.topicId}</p>}
          </div>
        </div>
        <div className="mt-5">
          {tagQuery.error ? (
            <Alert variant="error">Unable to load tags. {tagQuery.error}</Alert>
          ) : (
            <TagPicker
              tags={tags}
              selected={values.tagIds}
              onChange={(ids) => set('tagIds', ids)}
              onTagCreated={(tag) => setCreatedTags((current) => [...current, tag])}
            />
          )}
        </div>
      </SectionCard>

      <SectionCard title="Statement" description="Markdown-style text: blank lines, - bullets, `code`, **bold**" icon={<FileText />}>
        <div className="space-y-4">
          <TextArea label="Description" rows={8} value={values.description} error={errors.description} maxLength={20000}
            onChange={(event) => set('description', event.target.value)} />
          <TextArea label="Constraints" hint="One constraint per line." mono rows={3} value={values.constraints} maxLength={5000}
            onChange={(event) => set('constraints', event.target.value)} />
          <div className="grid gap-4 md:grid-cols-2">
            <TextArea label="Input Format" rows={3} value={values.inputFormat} maxLength={5000}
              onChange={(event) => set('inputFormat', event.target.value)} />
            <TextArea label="Output Format" rows={3} value={values.outputFormat} maxLength={5000}
              onChange={(event) => set('outputFormat', event.target.value)} />
          </div>
        </div>
      </SectionCard>

      <SectionCard title="Examples" description="Public worked examples shown to students" icon={<ListChecks />}>
        <ExamplesEditor examples={values.examples} onChange={(examples) => set('examples', examples)} error={errors.examples} />
      </SectionCard>

      <SectionCard title="Starter Code" description="Initial editor contents per language" icon={<Code2 />}>
        <StarterCodeEditor
          value={values.starter}
          onChange={(starter) => set('starter', starter)}
          drivers={values.drivers}
          onDriversChange={(drivers) => set('drivers', drivers)}
          driverError={errors.drivers}
        />
      </SectionCard>

      <SectionCard title="Test Cases" description="Stored for the judge; not executed in this phase" icon={<FlaskConical />}>
        {mode === 'create' ? (
          <div className="space-y-4">
            {values.testCases.map((testCase, index) => (
              <div key={testCase.key} role="group" aria-label={`Test case ${index + 1}`} className="rounded-xl border border-ink-200 bg-night/40 p-4">
                <div className="mb-3 flex items-center justify-between">
                  <p className="text-sm font-semibold text-ink-950">Test case {index + 1}</p>
                  <Button size="sm" variant="ghost" icon={<Trash2 className="size-3.5" aria-hidden />} aria-label={`Remove test case ${index + 1}`}
                    onClick={() => set('testCases', values.testCases.filter((t) => t.key !== testCase.key))}>
                    Remove
                  </Button>
                </div>
                <TestCaseFields
                  label={`Test case ${index + 1}`}
                  value={testCase}
                  onChange={(next) => set('testCases', values.testCases.map((t) => (t.key === testCase.key ? { ...t, ...next } : t)))}
                />
              </div>
            ))}
            {errors.testCases && <p className="text-[13px] text-danger" role="alert">{errors.testCases}</p>}
            <Button size="sm" variant="secondary" icon={<Plus className="size-3.5" aria-hidden />} disabled={values.testCases.length >= 50}
              onClick={() => set('testCases', [...values.testCases, emptyTestCase()])}>
              Add test case
            </Button>
          </div>
        ) : (
          testCasesLink && (
            <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <p className="text-sm text-ink-500">
                {testCasesLink.count} test case{testCasesLink.count === 1 ? '' : 's'} ({testCasesLink.hidden} hidden). Test
                cases are managed on their own page.
              </p>
              <ButtonLink to={testCasesLink.to} size="sm" variant="secondary" icon={<FlaskConical className="size-3.5" aria-hidden />}>
                Manage Test Cases
              </ButtonLink>
            </div>
          )
        )}
      </SectionCard>

      <SectionCard title="Judging" description="Limits for each run of the student's program" icon={<Gauge />}>
        <div className="grid gap-4 sm:grid-cols-2">
          <TextField label="Time limit (ms)" type="number" min={100} max={10000} step={100} value={values.timeLimitMs}
            onChange={(event) => set('timeLimitMs', event.target.value)} error={errors.limits}
            hint="Per test, for C++. Java gets 2x and Python 3x this time." />
          <TextField label="Memory limit (MB)" type="number" min={16} max={500} value={values.memoryLimitMb}
            onChange={(event) => set('memoryLimitMb', event.target.value)} />
        </div>
      </SectionCard>

      <SectionCard title="Publishing" icon={<Rocket />}>
        <Switch
          label="Published"
          description={values.isPublished ? 'Students can see and open this problem.' : 'Draft: only admins can see this problem.'}
          checked={values.isPublished}
          onChange={(checked) => set('isPublished', checked)}
        />
      </SectionCard>

      <div className="sticky bottom-0 z-10 -mx-1 flex flex-col-reverse gap-2 rounded-xl border border-ink-200 bg-surface/95 p-3 backdrop-blur sm:flex-row sm:justify-end">
        <ButtonLink to="/admin/problems" variant="secondary">
          Cancel
        </ButtonLink>
        <Button type="submit" loading={submitting} loadingText="Saving..." icon={<Save className="size-4" aria-hidden />}>
          {mode === 'create' ? 'Create Problem' : 'Save Changes'}
        </Button>
      </div>
    </form>
  )
}
