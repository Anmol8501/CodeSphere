import { ArrowLeft, Lock, Mail, ShieldCheck } from 'lucide-react'
import { useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { LogoMark } from '../../components/brand/Logo'
import { Alert } from '../../components/ui/Alert'
import { Button } from '../../components/ui/Button'
import { TextField } from '../../components/ui/TextField'
import { useAuth } from '../../hooks/useAuth'
import { useFlashMessage } from '../../hooks/useFlashMessage'
import { getErrorMessage } from '../../utils/errors'
import { compactErrors, validateEmail, validateRequired } from '../../utils/validation'

type FieldErrors = Partial<Record<'email' | 'password', string>>

/** Separate, restricted login for administrators (not linked from the public pages). */
export default function AdminLoginPage() {
  const { login } = useAuth()
  const flash = useFlashMessage()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({})
  const [formError, setFormError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

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
      // The backend rejects this unless the account's database role is ADMIN.
      await login({ email: email.trim(), password }, 'ADMIN')
    } catch (error) {
      setFormError(getErrorMessage(error))
      setPassword('')
      setSubmitting(false)
    }
  }

  return (
    <div className="relative flex min-h-svh items-center justify-center overflow-hidden bg-night px-4 py-10">
      <div className="bg-dot-grid absolute inset-0" aria-hidden />
      <div className="absolute top-1/4 left-1/2 size-[520px] -translate-x-1/2 rounded-full bg-brand-500/10 blur-3xl" aria-hidden />

      <div className="relative w-full max-w-[420px] animate-fade-in">
        <div className="mb-7 flex flex-col items-center text-center">
          <LogoMark className="size-12" />
          <p className="mt-4 inline-flex items-center gap-1.5 rounded-full border border-warning/30 bg-warning/10 px-3 py-1 text-xs font-semibold text-warning">
            <ShieldCheck className="size-3.5" /> Restricted area
          </p>
        </div>

        <div className="rounded-3xl border border-ink-200 bg-surface p-6 shadow-2xl shadow-black/60 sm:p-8">
          <h1 className="text-center text-2xl font-extrabold tracking-tight text-ink-950">
            CodeArena Admin Portal
          </h1>
          <p className="mt-1.5 text-center text-sm text-ink-500">
            Sign in with your administrator credentials.
          </p>

          <div className="mt-6 space-y-3">
            {flash && !formError && <Alert variant={flash.type}>{flash.message}</Alert>}
            {formError && (
              <Alert variant="error" onDismiss={() => setFormError(null)}>
                {formError}
              </Alert>
            )}
          </div>

          <form onSubmit={handleSubmit} noValidate className="mt-4 space-y-4">
            <TextField
              label="Admin Email"
              type="email"
              name="email"
              autoComplete="username"
              placeholder="admin@college.edu"
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
            />
            <Button
              type="submit"
                            size="lg"
              fullWidth
              loading={submitting}
              loadingText="Logging in..."
              icon={<ShieldCheck className="size-4" />}
            >
              Admin Login
            </Button>
          </form>
        </div>

        <Link
          to="/login"
          className="mt-6 flex items-center justify-center gap-1.5 text-sm font-medium text-ink-500 transition hover:text-brand-500"
        >
          <ArrowLeft className="size-4" /> Back to student / staff login
        </Link>
      </div>
    </div>
  )
}
