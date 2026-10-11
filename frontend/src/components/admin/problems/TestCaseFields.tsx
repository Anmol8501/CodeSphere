import { Switch } from '../../ui/Switch'
import { TextArea } from '../../ui/TextArea'

export interface TestCaseValue {
  input_data: string
  expected_output: string
  is_hidden: boolean
}

interface TestCaseFieldsProps {
  value: TestCaseValue
  onChange: (value: TestCaseValue) => void
  /** Prefix for accessible labels, e.g. "Test case 2". */
  label: string
  disabled?: boolean
}

/** Input / expected output / hidden toggle. Test data is stored exactly as typed. */
export function TestCaseFields({ value, onChange, label, disabled }: TestCaseFieldsProps) {
  return (
    <div className="space-y-3">
      <div className="grid gap-3 md:grid-cols-2">
        <TextArea label={`${label} input`} mono rows={3} value={value.input_data} disabled={disabled} maxLength={100000}
          onChange={(event) => onChange({ ...value, input_data: event.target.value })} />
        <TextArea label={`${label} expected output`} mono rows={3} value={value.expected_output} disabled={disabled} maxLength={100000}
          onChange={(event) => onChange({ ...value, expected_output: event.target.value })} />
      </div>
      <Switch
        label="Hidden test case"
        description={
          value.is_hidden
            ? 'Only admins and the future judge can see this case.'
            : 'Visible: students see it as a sample test on the problem page.'
        }
        checked={value.is_hidden}
        disabled={disabled}
        onChange={(is_hidden) => onChange({ ...value, is_hidden })}
      />
    </div>
  )
}
