import { Lock, Mail, User as UserIcon } from 'lucide-react'
import { useState, type ChangeEvent, type FormEvent } from 'react'
import { adminService } from '../../services/adminService'
import type { CreateStaffPayload } from '../../types/admin'
import type { User } from '../../types/auth'
import { getErrorMessage, getErrorStatus, getFieldErrors } from '../../utils/errors'
import {
  PASSWORD_MIN_LENGTH,
  compactErrors,
  validateEmail,
  validateFullName,
  validateNewPassword,
} from '../../utils/validation'
import { Alert } from '../ui/Alert'
import { Button } from '../ui/Button'
import { Modal } from '../ui/Modal'
import { TextField } from '../ui/TextField'

type Field = keyof CreateStaffPayload
const EMPTY: CreateStaffPayload = { full_name: '', email: '', password: '' }

interface CreateStaffModalProps {
  open: boolean
  onClose: () => void
  onCreated: (user: User) => void
}

export function CreateStaffModal({ open, onClose, onCreated }: CreateStaffModalProps) {
  const [values, setValues] = useState<CreateStaffPayload>(EMPTY)
  const [errors, setErrors] = useState<Partial<Record<Field, string>>>({})
  const [formError, setFormError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)

  const close = () => {
    if (saving) return
    setValues(EMPTY)
    setErrors({})
    setFormError(null)
    onClose()
  }

  const update = (field: Field) => (event: ChangeEvent<HTMLInputElement>) => {
    setValues((current) => ({ ...current, [field]: event.target.value }))
    if (errors[field]) setErrors((current) => ({ ...current, [field]: undefined }))
  }

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault()
    setFormError(null)
    const validationErrors = compactErrors({
      full_name: validateFullName(values.full_name),
      email: validateEmail(values.email),
      password: validateNewPassword(values.password),
    })
    setErrors(validationErrors)
    if (Object.keys(validationErrors).length > 0) return

    setSaving(true)
    try {
      const user = await adminService.createStaff({
        ...values,
        full_name: values.full_name.trim(),
        email: values.email.trim(),
      })
      setValues(EMPTY)
      onCreated(user)
    } catch (error) {
      const status = getErrorStatus(error)
      if (status === 409) setErrors({ email: getErrorMessage(error) })
      else if (status === 422) setErrors(getFieldErrors(error))
      else setFormError(getErrorMessage(error))
    } finally {
      setSaving(false)
    }
  }

  return (
    <Modal
      open={open}
      onClose={close}
      title="Add staff member"
      description="Share the password with the staff member securely. They can sign in via Staff Login."
      footer={
        <>
          <Button variant="secondary" onClick={close} disabled={saving}>
            Cancel
          </Button>
          <Button type="submit" form="create-staff-form" loading={saving} loadingText="Creating...">
            Create staff account
          </Button>
        </>
      }
    >
      {formError && (
        <Alert variant="error" className="mb-4">
          {formError}
        </Alert>
      )}
      <form id="create-staff-form" onSubmit={handleSubmit} noValidate className="space-y-4">
        <TextField
          label="Full Name"
          icon={<UserIcon />}
          value={values.full_name}
          onChange={update('full_name')}
          error={errors.full_name}
          placeholder="e.g. Dr. Priya Menon"
          autoComplete="off"
        />
        <TextField
          label="Staff Email"
          type="email"
          icon={<Mail />}
          value={values.email}
          onChange={update('email')}
          error={errors.email}
          placeholder="name@college.edu"
          autoComplete="off"
        />
        <TextField
          label="Temporary Password"
          type="password"
          icon={<Lock />}
          value={values.password}
          onChange={update('password')}
          error={errors.password}
          hint={`At least ${PASSWORD_MIN_LENGTH} characters, with a letter and a number.`}
          autoComplete="new-password"
        />
      </form>
    </Modal>
  )
}
