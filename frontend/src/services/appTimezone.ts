import type { ApiResponse } from '../types/api'
import { api, unwrap } from './api'

/**
 * The server's application timezone (APP_TIMEZONE). Calendar days shown in the
 * UI ("Today", "Yesterday", the heatmap) use it, so they always match how the
 * server counts streaks. Fetched once per page load; falls back to the
 * browser's zone only if the server cannot be reached.
 */
let pending: Promise<string> | null = null

export function getAppTimezone(): Promise<string> {
  pending ??= unwrap(api.get<ApiResponse<{ status: string; timezone?: string }>>('/health'))
    .then((data) => data.timezone ?? Intl.DateTimeFormat().resolvedOptions().timeZone)
    .catch(() => {
      pending = null
      return Intl.DateTimeFormat().resolvedOptions().timeZone
    })
  return pending
}
