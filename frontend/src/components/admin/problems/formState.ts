import type { AdminProblem, ProblemCreatePayload, TestCasePayload } from '../../../types/adminProblem'
import type { Difficulty, Language } from '../../../types/problem'

export const LANGUAGES: Language[] = ['CPP', 'JAVA', 'PYTHON']

/** Suggested starter code for a new problem (editable, never executed). */
export const DEFAULT_STARTER: Record<Language, string> = {
  CPP: 'class Solution {\npublic:\n    // Write your solution here\n};\n',
  JAVA: 'class Solution {\n    public void solve() {\n        // Write your solution here\n    }\n}\n',
  PYTHON: 'class Solution:\n    def solve(self):\n        # Write your solution here\n        pass\n',
}

let keySeq = 0
/** Stable React keys for rows that have no database id yet. */
export const nextKey = () => `row-${++keySeq}`

export interface ExampleDraft {
  key: string
  input: string
  output: string
  explanation: string
}

export interface TestCaseDraft {
  key: string
  input_data: string
  expected_output: string
  is_hidden: boolean
}

export interface ProblemFormValues {
  title: string
  slug: string
  /** Once the admin edits the slug it stops following the title. */
  slugTouched: boolean
  description: string
  difficulty: Difficulty
  topicId: string
  tagIds: number[]
  constraints: string
  inputFormat: string
  outputFormat: string
  examples: ExampleDraft[]
  starter: Record<Language, string>
  /** Hidden execution harness per language (blank = the code is a full program). */
  drivers: Record<Language, string>
  timeLimitMs: string
  memoryLimitMb: string
  testCases: TestCaseDraft[]
  isPublished: boolean
}

export type FormErrors = Partial<
  Record<'title' | 'slug' | 'description' | 'topicId' | 'examples' | 'testCases' | 'limits' | 'drivers', string>
>

export const USER_CODE_MARKER = '{{USER_CODE}}'

export const emptyExample = (): ExampleDraft => ({ key: nextKey(), input: '', output: '', explanation: '' })
export const emptyTestCase = (): TestCaseDraft => ({ key: nextKey(), input_data: '', expected_output: '', is_hidden: true })

export function newProblemValues(): ProblemFormValues {
  return {
    title: '',
    slug: '',
    slugTouched: false,
    description: '',
    difficulty: 'EASY',
    topicId: '',
    tagIds: [],
    constraints: '',
    inputFormat: '',
    outputFormat: '',
    examples: [emptyExample()],
    starter: { ...DEFAULT_STARTER },
    drivers: { CPP: '', JAVA: '', PYTHON: '' },
    timeLimitMs: '2000',
    memoryLimitMb: '256',
    testCases: [{ ...emptyTestCase(), is_hidden: false }],
    isPublished: false,
  }
}

export function valuesFromProblem(problem: AdminProblem): ProblemFormValues {
  const starter: Record<Language, string> = { CPP: '', JAVA: '', PYTHON: '' }
  const drivers: Record<Language, string> = { CPP: '', JAVA: '', PYTHON: '' }
  for (const code of problem.starter_codes) {
    starter[code.language] = code.starter_code
    drivers[code.language] = code.driver_code ?? ''
  }
  return {
    title: problem.title,
    slug: problem.slug,
    slugTouched: true,
    description: problem.description,
    difficulty: problem.difficulty,
    topicId: String(problem.topic.id),
    tagIds: problem.tags.map((t) => t.id),
    constraints: problem.constraints,
    inputFormat: problem.input_format,
    outputFormat: problem.output_format,
    examples: problem.examples.map((e) => ({
      key: nextKey(),
      input: e.input,
      output: e.output,
      explanation: e.explanation ?? '',
    })),
    starter,
    drivers,
    timeLimitMs: String(problem.time_limit_ms),
    memoryLimitMb: String(Math.round(problem.memory_limit_kb / 1024)),
    testCases: [],
    isPublished: problem.is_published,
  }
}

/** Same rules as the backend slugify ("Two Sum!" -> "two-sum"). */
export function slugify(value: string): string {
  return value
    .normalize('NFKD')
    .replace(/[^\x20-\x7e]/g, '')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .slice(0, 160)
    .replace(/-+$/, '')
}

const SLUG_PATTERN = /^[a-z0-9]+(?:-[a-z0-9]+)*$/

const isBlank = (value: string) => value.trim() === ''

export function validate(values: ProblemFormValues, mode: 'create' | 'edit'): FormErrors {
  const errors: FormErrors = {}
  if (values.title.trim().length < 3) errors.title = 'Title must be at least 3 characters.'
  const slug = values.slug.trim()
  if (slug && !SLUG_PATTERN.test(slug)) errors.slug = 'Use lowercase letters, numbers and single hyphens.'
  if (!slug && !slugify(values.title)) errors.slug = 'Enter a slug.'
  if (values.description.trim().length < 10) errors.description = 'Description must be at least 10 characters.'
  if (!values.topicId) errors.topicId = 'Select a topic.'
  const timeLimit = Number(values.timeLimitMs)
  const memoryMb = Number(values.memoryLimitMb)
  if (!Number.isInteger(timeLimit) || timeLimit < 100 || timeLimit > 10000) errors.limits = 'Time limit must be 100-10000 ms.'
  else if (!Number.isInteger(memoryMb) || memoryMb < 16 || memoryMb > 500) errors.limits = 'Memory limit must be 16-500 MB.'
  const badDriver = LANGUAGES.find((lang) => values.drivers[lang].trim() && values.drivers[lang].split(USER_CODE_MARKER).length !== 2)
  if (badDriver) errors.drivers = `The ${badDriver} harness must contain ${USER_CODE_MARKER} exactly once.`

  const partialExample = values.examples.some(
    (e) => (isBlank(e.input) || isBlank(e.output)) && !(isBlank(e.input) && isBlank(e.output) && isBlank(e.explanation)),
  )
  if (partialExample) errors.examples = 'Each example needs both an input and an output.'

  if (mode === 'create') {
    const partialCase = values.testCases.some((t) => isBlank(t.expected_output) && !isBlank(t.input_data))
    if (partialCase) errors.testCases = 'Each test case needs an expected output.'
  }
  return errors
}

export function toTestCasePayload(draft: Omit<TestCaseDraft, 'key'>): TestCasePayload {
  return { input_data: draft.input_data, expected_output: draft.expected_output, is_hidden: draft.is_hidden }
}

export function toPayload(values: ProblemFormValues): ProblemCreatePayload {
  return {
    title: values.title.trim(),
    slug: values.slug.trim() || null,
    description: values.description,
    difficulty: values.difficulty,
    topic_id: Number(values.topicId),
    tag_ids: values.tagIds,
    constraints: values.constraints,
    input_format: values.inputFormat,
    output_format: values.outputFormat,
    time_limit_ms: Number(values.timeLimitMs),
    memory_limit_kb: Number(values.memoryLimitMb) * 1024,
    examples: values.examples
      .filter((e) => !isBlank(e.input) || !isBlank(e.output))
      .map((e) => ({ input: e.input, output: e.output, explanation: e.explanation.trim() || null })),
    starter_codes: LANGUAGES.filter((lang) => !isBlank(values.starter[lang])).map((lang) => ({
      language: lang,
      starter_code: values.starter[lang],
      driver_code: values.drivers[lang].trim() ? values.drivers[lang] : null,
    })),
    test_cases: values.testCases.filter((t) => !isBlank(t.expected_output)).map(toTestCasePayload),
    is_published: values.isPublished,
  }
}
