import { Lock, Mail, User as UserIcon } from 'lucide-react'
import { useState, type ChangeEvent, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Alert } from '../../components/ui/Alert'
import { Button } from '../../components/ui/Button'
import { TextField } from '../../components/ui/TextField'
import { useAuth } from '../../hooks/useAuth'
import { AuthLayout } from '../../layouts/AuthLayout'
import { getErrorMessage, getErrorStatus, getFieldErrors } from '../../utils/errors'
import {
  PASSWORD_MIN_LENGTH,
  compactErrors,
  validateEmail,
  validateFullName,
  validateNewPassword,
} from '../../utils/validation'

type Field = 'full_name' | 'email' | 'password' | 'confirm_password'
type FormValues = Record<Field, string>

const EMPTY_FORM: FormValues = { full_name: '', email: '', password: '', confirm_password: '' }

function validate(values: FormValues) {
  return compactErrors({
    full_name: validateFullName(values.full_name),
    email: validateEmail(values.email),
    password: validateNewPassword(values.password),
    confirm_password: !values.confirm_password
      ? 'Please confirm your password.'
      : values.confirm_password !== values.password
        ? 'Passwords do not match.'
        : undefined,
  })
}

export default function RegisterPage() {
  const { register } = useAuth()
  const navigate = useNavigate()
  const [values, setValues] = useState<FormValues>(EMPTY_FORM)
  const [errors, setErrors] = useState<Partial<Record<Field, string>>>({})
  const [formError, setFormError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  const update = (field: Field) => (event: ChangeEvent<HTMLInputElement>) => {
    setValues((current) => ({ ...current, [field]: event.target.value }))
    if (errors[field]) setErrors((current) => ({ ...current, [field]: undefined }))
  }

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault()
    setFormError(null)

    const validationErrors = validate(values)
    setErrors(validationErrors)
    if (Object.keys(validationErrors).length > 0) return

    setSubmitting(true)
    try {
      const user = await register({
        ...values,
        full_name: values.full_name.trim(),
        email: values.email.trim(),
      })
      navigate('/login', { replace: true, state: { registered: true, email: user.email } })
    } catch (error) {
      const status = getErrorStatus(error)
      if (status === 409) {
        setErrors({ email: getErrorMessage(error) })
      } else if (status === 422) {
        const serverErrors = getFieldErrors(error)
        setErrors(serverErrors)
        if (!Object.keys(serverErrors).some((key) => key in EMPTY_FORM)) {
          setFormError(getErrorMessage(error))
        }
      } else {
        setFormError(getErrorMessage(error))
      }
      setSubmitting(false)
    }
  }

  return (
    <AuthLayout>
      <div className="mb-6">
        <p className="mb-2 font-mono text-xs font-medium text-brand-500">{'<new_student />'}</p>
        <h1 className="text-2xl font-extrabold tracking-tight text-ink-950 sm:text-[28px]">
          Create your CodeArena account
        </h1>
        <p className="mt-1.5 text-sm text-ink-500">Join as a student and start your coding journey.</p>
      </div>

      {formError && (
        <Alert variant="error" className="mb-4" onDismiss={() => setFormError(null)}>
          {formError}
        </Alert>
      )}

      <form onSubmit={handleSubmit} noValidate className="space-y-4">
        <TextField
          label="Full Name"
          name="full_name"
          autoComplete="name"
          placeholder="e.g. Asha Kumar"
          icon={<UserIcon />}
          value={values.full_name}
          onChange={update('full_name')}
          error={errors.full_name}
          disabled={submitting}
        />
        <TextField
          label="College Email"
          type="email"
          name="email"
          autoComplete="email"
          placeholder="you@college.edu"
          icon={<Mail />}
          value={values.email}
          onChange={update('email')}
          error={errors.email}
          disabled={submitting}
        />
        <TextField
          label="Password"
          type="password"
          name="password"
          autoComplete="new-password"
          placeholder="Create a password"
          icon={<Lock />}
          value={values.password}
          onChange={update('password')}
          error={errors.password}
          hint={`At least ${PASSWORD_MIN_LENGTH} characters, with a letter and a number.`}
          disabled={submitting}
        />
        <TextField
          label="Confirm Password"
          type="password"
          name="confirm_password"
          autoComplete="new-password"
          placeholder="Re-enter your password"
          icon={<Lock />}
          value={values.confirm_password}
          onChange={update('confirm_password')}
          error={errors.confirm_password}
          disabled={submitting}
        />

        <Button type="submit" size="lg" fullWidth loading={submitting} loadingText="Creating account...">
          Create Account
        </Button>
      </form>

      <p className="mt-6 border-t border-ink-200 pt-5 text-center text-sm text-ink-500">
        Already have an account?{' '}
        <Link to="/login" className="font-semibold text-brand-500 hover:text-brand-300">
          Login
        </Link>
      </p>
    </AuthLayout>
  )
}
