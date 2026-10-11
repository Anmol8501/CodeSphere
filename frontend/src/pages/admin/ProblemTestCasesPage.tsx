import { ArrowLeft, EyeOff, FlaskConical, Pencil, Plus, Save, Trash2 } from 'lucide-react'
import { useCallback, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { ProblemStatusBadge } from '../../components/admin/problems/ProblemStatusBadge'
import { TestCaseFields, type TestCaseValue } from '../../components/admin/problems/TestCaseFields'
import { Alert } from '../../components/ui/Alert'
import { Badge } from '../../components/ui/Badge'
import { Button, ButtonLink } from '../../components/ui/Button'
import { Card, SectionCard } from '../../components/ui/Card'
import { EmptyState } from '../../components/ui/EmptyState'
import { ErrorState } from '../../components/ui/ErrorState'
import { PageSkeleton } from '../../components/ui/LoadingState'
import { Modal } from '../../components/ui/Modal'
import { PageHeader } from '../../components/ui/PageHeader'
import { useApiQuery } from '../../hooks/useApiQuery'
import { adminProblemService } from '../../services/adminProblemService'
import type { AdminProblem, TestCase } from '../../types/adminProblem'
import { getErrorMessage } from '../../utils/errors'

const EMPTY: TestCaseValue = { input_data: '', expected_output: '', is_hidden: true }

function Preview({ label, value }: { label: string; value: string }) {
  return (
    <div className="min-w-0">
      <p className="mb-1 font-mono text-[10px] tracking-[0.2em] text-ink-400 uppercase">{label}</p>
      <pre className="max-h-40 overflow-auto rounded-lg bg-night px-3 py-2 font-mono text-[12px] whitespace-pre-wrap text-ink-900 ring-1 ring-ink-200">
        {value || '(empty)'}
      </pre>
    </div>
  )
}

/** /admin/problems/:id/test-cases. Stored for the future judge; nothing runs here. */
export default function ProblemTestCasesPage() {
  const { id } = useParams()
  const problemId = Number(id)
  const validId = Number.isInteger(problemId) && problemId > 0

  // An invalid id never reaches the API; the page shows "Problem not found." instead.
  const fetchProblem = useCallback(
    (): Promise<AdminProblem> => (validId ? adminProblemService.get(problemId) : Promise.reject(new Error('invalid id'))),
    [problemId, validId],
  )
  const fetchCases = useCallback(
    (): Promise<TestCase[]> => (validId ? adminProblemService.listTestCases(problemId) : Promise.reject(new Error('invalid id'))),
    [problemId, validId],
  )
  const problem = useApiQuery(fetchProblem)
  const cases = useApiQuery(fetchCases)

  const [notice, setNotice] = useState<{ type: 'success' | 'error'; message: string } | null>(null)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [draft, setDraft] = useState<TestCaseValue>(EMPTY)
  const [newCase, setNewCase] = useState<TestCaseValue>(EMPTY)
  const [saving, setSaving] = useState(false)
  const [deleteTarget, setDeleteTarget] = useState<{ testCase: TestCase; index: number } | null>(null)

  const run = async (action: () => Promise<unknown>, success: string) => {
    setSaving(true)
    setNotice(null)
    try {
      await action()
      setNotice({ type: 'success', message: success })
      cases.reload()
      return true
    } catch (err) {
      setNotice({ type: 'error', message: getErrorMessage(err) })
      return false
    } finally {
      setSaving(false)
    }
  }

  const back = (
    <Link to="/admin/problems" className="mb-4 inline-flex items-center gap-1.5 text-sm font-semibold text-ink-500 transition hover:text-brand-400">
      <ArrowLeft className="size-4" aria-hidden /> Back to Problem Management
    </Link>
  )

  if (!validId) {
    return (
      <div>
        {back}
        <ErrorState title="Unable to load test cases." message="Problem not found." />
      </div>
    )
  }
  if ((problem.loading && !problem.data) || (cases.loading && !cases.data)) return <PageSkeleton />
  if (problem.error || cases.error || !problem.data || !cases.data) {
    return (
      <div>
        {back}
        <ErrorState
          title="Unable to load test cases."
          message={problem.error ?? cases.error ?? 'No data received.'}
          onRetry={() => {
            problem.reload()
            cases.reload()
          }}
        />
      </div>
    )
  }

  const hidden = cases.data.filter((c) => c.is_hidden).length

  return (
    <div className="animate-fade-in">
      {back}
      <PageHeader
        eyebrow="Admin · Test Cases"
        title={problem.data.title}
        description={`${cases.data.length} test case${cases.data.length === 1 ? '' : 's'} · ${hidden} hidden · ${cases.data.length - hidden} visible`}
        action={
          <>
            <ProblemStatusBadge status={problem.data.status} />
            <ButtonLink to={`/admin/problems/${problem.data.id}/edit`} size="sm" variant="secondary" icon={<Pencil className="size-3.5" aria-hidden />}>
              Edit Problem
            </ButtonLink>
          </>
        }
      />

      <Alert variant="info" className="mb-4">
        Test cases are stored for the judge that arrives in a later phase; nothing is executed yet. Hidden cases are never sent to
        students. Visible cases appear as sample tests on the problem page.
      </Alert>
      {notice && (
        <Alert variant={notice.type} className="mb-4" onDismiss={() => setNotice(null)}>
          {notice.message}
        </Alert>
      )}

      <div className="space-y-4">
        {cases.data.length === 0 && (
          <EmptyState icon={<FlaskConical />} title="No test cases yet." description="Add the first test case below." />
        )}
        {cases.data.map((testCase, index) => {
          const editing = editingId === testCase.id
          return (
            <Card key={testCase.id} as="article" aria-labelledby={`case-${testCase.id}`} className="p-4 sm:p-5">
              <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
                <h2 id={`case-${testCase.id}`} className="flex items-center gap-2 font-mono text-xs font-semibold tracking-[0.14em] text-ink-950 uppercase">
                  Test case {index + 1}
                  {testCase.is_hidden ? (
                    <Badge tone="neutral" mono>
                      <EyeOff className="size-3" aria-hidden /> Hidden
                    </Badge>
                  ) : (
                    <Badge tone="info" mono>Visible</Badge>
                  )}
                </h2>
                {!editing && (
                  <div className="flex gap-1.5">
                    <Button size="sm" variant="secondary" icon={<Pencil className="size-3.5" aria-hidden />} aria-label={`Edit test case ${index + 1}`}
                      onClick={() => {
                        setEditingId(testCase.id)
                        setDraft({ input_data: testCase.input_data, expected_output: testCase.expected_output, is_hidden: testCase.is_hidden })
                      }}>
                      Edit
                    </Button>
                    <Button size="sm" variant="danger" icon={<Trash2 className="size-3.5" aria-hidden />} aria-label={`Delete test case ${index + 1}`}
                      onClick={() => setDeleteTarget({ testCase, index })}>
                      Delete
                    </Button>
                  </div>
                )}
              </div>

              {editing ? (
                <>
                  <TestCaseFields label={`Test case ${index + 1}`} value={draft} onChange={setDraft} disabled={saving} />
                  <div className="mt-4 flex justify-end gap-2">
                    <Button size="sm" variant="secondary" disabled={saving} onClick={() => setEditingId(null)}>
                      Cancel
                    </Button>
                    <Button size="sm" icon={<Save className="size-3.5" aria-hidden />} loading={saving} disabled={!draft.expected_output.trim()}
                      onClick={async () => {
                        if (await run(() => adminProblemService.updateTestCase(testCase.id, draft), `Test case ${index + 1} updated.`)) {
                          setEditingId(null)
                        }
                      }}>
                      Save
                    </Button>
                  </div>
                </>
              ) : (
                <div className="grid gap-3 md:grid-cols-2">
                  <Preview label="Input" value={testCase.input_data} />
                  <Preview label="Expected output" value={testCase.expected_output} />
                </div>
              )}
            </Card>
          )
        })}

        <SectionCard title="Add test case" icon={<Plus />}>
          <TestCaseFields label="New test case" value={newCase} onChange={setNewCase} disabled={saving} />
          <div className="mt-4 flex justify-end">
            <Button icon={<Plus className="size-4" aria-hidden />} loading={saving} disabled={!newCase.expected_output.trim()}
              onClick={async () => {
                if (await run(() => adminProblemService.addTestCase(problemId, newCase), 'Test case added.')) setNewCase(EMPTY)
              }}>
              Add Test Case
            </Button>
          </div>
        </SectionCard>
      </div>

      <Modal
        open={deleteTarget !== null}
        onClose={() => !saving && setDeleteTarget(null)}
        title="Delete test case?"
        description={`Test case ${deleteTarget ? deleteTarget.index + 1 : ''} will be permanently removed.`}
        footer={
          <>
            <Button variant="secondary" disabled={saving} onClick={() => setDeleteTarget(null)}>
              Cancel
            </Button>
            <Button variant="danger" loading={saving} loadingText="Deleting..."
              onClick={async () => {
                if (!deleteTarget) return
                await run(() => adminProblemService.deleteTestCase(deleteTarget.testCase.id), `Test case ${deleteTarget.index + 1} deleted.`)
                setDeleteTarget(null)
              }}>
              Delete
            </Button>
          </>
        }
      >
        <p className="text-sm text-ink-500">This cannot be undone.</p>
      </Modal>
    </div>
  )
}
