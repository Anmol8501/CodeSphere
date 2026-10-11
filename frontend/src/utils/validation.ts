// Client-side validation mirrors the backend rules so users get instant
// feedback. The backend still validates everything.

export const PASSWORD_MIN_LENGTH = 8

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/

export function validateEmail(email: string): string | undefined {
  if (!email.trim()) return 'Email is required.'
  if (!EMAIL_PATTERN.test(email.trim())) return 'Please enter a valid email address.'
  return undefined
}

export function validateRequired(value: string, label: string): string | undefined {
  return value.trim() ? undefined : `${label} is required.`
}

export function validateFullName(name: string): string | undefined {
  const trimmed = name.trim()
  if (!trimmed) return 'Full name is required.'
  if (trimmed.length < 2) return 'Full name must be at least 2 characters long.'
  if (trimmed.length > 120) return 'Full name must be at most 120 characters long.'
  return undefined
}

export function validateNewPassword(password: string): string | undefined {
  if (!password) return 'Password is required.'
  if (password.length < PASSWORD_MIN_LENGTH)
    return `Password must be at least ${PASSWORD_MIN_LENGTH} characters long.`
  if (password.length > 72) return 'Password is too long (maximum 72 characters).'
  if (!/[A-Za-z]/.test(password) || !/\d/.test(password))
    return 'Password must contain at least one letter and one number.'
  return undefined
}

/** Remove keys whose value is undefined, so `Object.keys(errors).length` means "has errors". */
export function compactErrors<T extends Record<string, string | undefined>>(
  errors: T,
): Partial<Record<keyof T, string>> {
  return Object.fromEntries(
    Object.entries(errors).filter(([, message]) => Boolean(message)),
  ) as Partial<Record<keyof T, string>>
}
