import { Lock, Mail, ShieldCheck } from 'lucide-react'
import { useState, type FormEvent } from 'react'
import { Link, useLocation, useSearchParams } from 'react-router-dom'
import { RoleTabs, type PublicLoginRole } from '../../components/auth/RoleTabs'
import { Alert } from '../../components/ui/Alert'
import { Button } from '../../components/ui/Button'
import { TextField } from '../../components/ui/TextField'
import { useAuth } from '../../hooks/useAuth'
import { useFlashMessage } from '../../hooks/useFlashMessage'
import { AuthLayout } from '../../layouts/AuthLayout'
import { getErrorMessage } from '../../utils/errors'
import { compactErrors, validateEmail, validateRequired } from '../../utils/validation'

interface LoginLocationState {
  from?: string
  registered?: boolean
  email?: string
}

type FieldErrors = Partial<Record<'email' | 'password', string>>

export default function LoginPage() {
  const { login } = useAuth()
  const location = useLocation()
  const state = (location.state as LoginLocationState | null) ?? {}
  const flash = useFlashMessage()

  // ?role=staff selects the staff tab (used by the "Staff Login" header link).
  const [searchParams, setSearchParams] = useSearchParams()
  const role: PublicLoginRole = searchParams.get('role') === 'staff' ? 'STAFF' : 'STUDENT'
  const isStaff = role === 'STAFF'

  const [email, setEmail] = useState(state.email ?? '')
  const [password, setPassword] = useState('')
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({})
  const [formError, setFormError] = useState<string | null>(null)
  const [showForgotInfo, setShowForgotInfo] = useState(false)
  const [submitting, setSubmitting] = useState(false)

  const changeRole = (next: PublicLoginRole) => {
    setSearchParams(next === 'STAFF' ? { role: 'staff' } : {}, { replace: true, state: location.state })
    setFormError(null)
    setFieldErrors({})
    setShowForgotInfo(false)
  }

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault()
    setFormError(null)

    const errors = compactErrors({
      email: validateEmail(email),
      password: validateRequired(password, 'Password'),
    })
    setFieldErrors(errors)
    if (Object.keys(errors).length > 0) return

    setSubmitting(true)
    try {
      // On success, GuestRoute notices the logged-in user and redirects to the dashboard.
      await login({ email: email.trim(), password }, role)
    } catch (error) {
      setFormError(getErrorMessage(error))
      setPassword('')
      setSubmitting(false)
    }
  }

  return (
    <AuthLayout>
      <div className="mb-6">
        <h1 className="text-2xl font-extrabold tracking-tight text-ink-950 sm:text-[28px]">
          Welcome Back <span aria-hidden>👋</span>
        </h1>
        <p className="mt-1.5 text-sm text-ink-500">Login to continue to CodeArena</p>
      </div>

      <RoleTabs value={role} onChange={changeRole} />

      <div className="mt-6 space-y-3">
        {state.registered && !formError && (
          <Alert variant="success">Account created successfully. Please login to continue.</Alert>
        )}
        {flash && !formError && <Alert variant={flash.type}>{flash.message}</Alert>}
        {formError && (
          <Alert variant="error" onDismiss={() => setFormError(null)}>
            {formError}
          </Alert>
        )}
      </div>

      <form onSubmit={handleSubmit} noValidate className="mt-4 space-y-4">
        <h2 className="text-[15px] font-bold text-ink-800">{isStaff ? 'Staff Login' : 'Student Login'}</h2>

        <TextField
          label={isStaff ? 'Staff Email' : 'Email'}
          type="email"
          name="email"
          autoComplete="email"
          placeholder={isStaff ? 'name@college.edu' : 'you@college.edu'}
          icon={<Mail />}
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          error={fieldErrors.email}
          disabled={submitting}
        />

        <TextField
          label="Password"
          type="password"
          name="password"
          autoComplete="current-password"
          placeholder="Enter your password"
          icon={<Lock />}
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          error={fieldErrors.password}
          disabled={submitting}
          labelAction={
            <button
              type="button"
              onClick={() => setShowForgotInfo((value) => !value)}
              className="text-[13px] font-semibold text-brand-500 hover:text-brand-300"
            >
              Forgot Password?
            </button>
          }
        />

        {showForgotInfo && (
          <Alert variant="info" onDismiss={() => setShowForgotInfo(false)}>
            Self-service password reset is coming soon. For now, please contact your administrator to
            reset your password.
          </Alert>
        )}

        <Button type="submit" size="lg" fullWidth loading={submitting} loadingText="Logging in...">
          {isStaff ? 'Staff Login' : 'Login'}
        </Button>
      </form>

      <div className="mt-6 border-t border-ink-200 pt-5 text-center text-sm">
        {isStaff ? (
          <p className="flex items-center justify-center gap-2 text-ink-500">
            <ShieldCheck className="size-4 shrink-0 text-ink-400" />
            Staff accounts are created by the administrator.
          </p>
        ) : (
          <p className="text-ink-500">
            Don't have an account?{' '}
            <Link to="/register" className="font-semibold text-brand-500 hover:text-brand-300">
              Register now
            </Link>
          </p>
        )}
      </div>
    </AuthLayout>
  )
}
