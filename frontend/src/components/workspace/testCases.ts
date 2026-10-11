import type { SampleTestCase } from '../../types/problem'
import type { CustomTestCase } from '../../types/workspace'

export interface TestCaseSelection {
  id: string
  label: string
  input: string
  expected: string
}

/** Public samples first ("Case N"), then the student's local custom cases. */
export function buildCases(samples: SampleTestCase[], custom: CustomTestCase[]): TestCaseSelection[] {
  return [
    ...samples.map((s, i) => ({ id: `sample-${i}`, label: `Case ${i + 1}`, input: s.input_data, expected: s.expected_output })),
    ...custom.map((c, i) => ({ id: c.id, label: `Custom ${i + 1}`, input: c.input, expected: c.expected })),
  ]
}
