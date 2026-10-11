import { ArrowLeft } from 'lucide-react'
import { useCallback, useMemo } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { ProblemForm } from '../../components/admin/problems/ProblemForm'
import { newProblemValues, toPayload, valuesFromProblem, type ProblemFormValues } from '../../components/admin/problems/formState'
import { ProblemStatusBadge } from '../../components/admin/problems/ProblemStatusBadge'
import { ErrorState } from '../../components/ui/ErrorState'
import { PageSkeleton } from '../../components/ui/LoadingState'
import { PageHeader } from '../../components/ui/PageHeader'
import { useApiQuery } from '../../hooks/useApiQuery'
import { adminProblemService } from '../../services/adminProblemService'
import { topicService } from '../../services/topicService'
import type { AdminProblem } from '../../types/adminProblem'

export interface ProblemsPageNotice {
  notice: string
}

/** /admin/problems/new and /admin/problems/:id/edit */
export default function ProblemEditorPage() {
  const { id } = useParams()
  const mode = id === undefined ? 'create' : 'edit'
  const parsedId = Number(id)
  const problemId = mode === 'edit' && Number.isInteger(parsedId) && parsedId > 0 ? parsedId : null
  const invalidId = mode === 'edit' && problemId === null
  const navigate = useNavigate()

  const topics = useApiQuery(topicService.list)
  const fetchProblem = useCallback(
    (): Promise<AdminProblem | null> => (problemId === null ? Promise.resolve(null) : adminProblemService.get(problemId)),
    [problemId],
  )
  const problem = useApiQuery(fetchProblem)
  const initialValues = useMemo(
    () => (problem.data ? valuesFromProblem(problem.data) : newProblemValues()),
    [problem.data],
  )

  const submit = async (values: ProblemFormValues) => {
    const payload = toPayload(values)
    if (mode === 'create') {
      const created = await adminProblemService.create(payload)
      navigate('/admin/problems', { state: { notice: `Problem "${created.title}" created.` } satisfies ProblemsPageNotice })
    } else if (problemId !== null) {
      const { test_cases: _ignored, ...update } = payload
      const saved = await adminProblemService.update(problemId, update)
      navigate('/admin/problems', { state: { notice: `Problem "${saved.title}" saved.` } satisfies ProblemsPageNotice })
    }
  }

  const back = (
    <Link to="/admin/problems" className="mb-4 inline-flex items-center gap-1.5 text-sm font-semibold text-ink-500 transition hover:text-brand-400">
      <ArrowLeft className="size-4" aria-hidden /> Back to Problem Management
    </Link>
  )

  if (invalidId) {
    return (
      <div>
        {back}
        <ErrorState title="Unable to load problem." message="Problem not found." />
      </div>
    )
  }
  if ((topics.loading && !topics.data) || (problem.loading && !problem.data && mode === 'edit')) return <PageSkeleton />
  const loadError = topics.error ?? problem.error
  if (loadError || !topics.data || (mode === 'edit' && !problem.data)) {
    return (
      <div>
        {back}
        <ErrorState
          title={mode === 'edit' ? 'Unable to load problem.' : 'Unable to load topics.'}
          message={loadError ?? 'No data received.'}
          onRetry={() => {
            topics.reload()
            problem.reload()
          }}
        />
      </div>
    )
  }

  return (
    <div className="animate-fade-in">
      {back}
      <PageHeader
        eyebrow="Admin · Problems"
        title={mode === 'create' ? 'Create Problem' : `Edit: ${problem.data?.title}`}
        description={
          mode === 'create'
            ? 'Write the statement, examples, starter code and test cases. Save as a draft or publish right away.'
            : 'Update the problem. Students see changes as soon as you save.'
        }
        action={problem.data && <ProblemStatusBadge status={problem.data.status} />}
      />
      <ProblemForm
        key={problem.data?.updated_at ?? 'new'}
        mode={mode}
        initialValues={initialValues}
        topics={topics.data}
        onSubmit={submit}
        testCasesLink={
          problem.data
            ? {
                to: `/admin/problems/${problem.data.id}/test-cases`,
                count: problem.data.test_case_count,
                hidden: problem.data.hidden_test_case_count,
              }
            : undefined
        }
      />
    </div>
  )
}
