import axios from 'axios'
import type { ApiErrorBody } from '../types/api'

export const NETWORK_ERROR_MESSAGE = 'Unable to connect to the server.'
export const SESSION_EXPIRED_MESSAGE = 'Your session has expired. Please login again.'

function getErrorBody(error: unknown): Partial<ApiErrorBody> | undefined {
  if (axios.isAxiosError(error)) {
    const data = error.response?.data
    if (data && typeof data === 'object') return data as Partial<ApiErrorBody>
  }
  return undefined
}

/** Turn any thrown value into a message that is safe to show to users. */
export function getErrorMessage(
  error: unknown,
  fallback = 'Something went wrong. Please try again.',
): string {
  if (axios.isAxiosError(error)) {
    if (!error.response) {
      return error.code === 'ECONNABORTED'
        ? 'The server took too long to respond. Please try again.'
        : NETWORK_ERROR_MESSAGE
    }
    const body = getErrorBody(error)
    if (typeof body?.message === 'string' && body.message) return body.message
    if (error.response.status >= 500) {
      return 'Something went wrong on our side. Please try again later.'
    }
  }
  return fallback
}

/** Map backend validation errors to `{ fieldName: message }` for forms. */
export function getFieldErrors(error: unknown): Record<string, string> {
  const result: Record<string, string> = {}
  for (const item of getErrorBody(error)?.errors ?? []) {
    if (item.field && !result[item.field]) result[item.field] = item.message
  }
  return result
}

export function getErrorStatus(error: unknown): number | undefined {
  return axios.isAxiosError(error) ? error.response?.status : undefined
}
