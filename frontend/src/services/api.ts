import axios, { type AxiosResponse } from 'axios'
import type { ApiErrorBody, ApiResponse } from '../types/api'
import { SESSION_EXPIRED_MESSAGE } from '../utils/errors'
import { tokenStorage } from '../utils/tokenStorage'

export const SESSION_EXPIRED_EVENT = 'codearena:session-expired'

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api',
  timeout: 15000,
  headers: { 'Content-Type': 'application/json' },
})

// Attach the JWT to every request when the user is logged in.
api.interceptors.request.use((config) => {
  const token = tokenStorage.get()
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// A 401 on an authenticated request means the token expired or became invalid
// (for example the account was deactivated). Clear it and tell the app.
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (axios.isAxiosError(error) && error.response?.status === 401) {
      const sentToken = Boolean(error.config?.headers?.Authorization)
      const isLoginCall = error.config?.url?.includes('/auth/login')
      if (sentToken && !isLoginCall) {
        tokenStorage.clear()
        const body = error.response.data as Partial<ApiErrorBody> | undefined
        const message =
          body?.message && !body.message.startsWith('Invalid authentication')
            ? body.message
            : SESSION_EXPIRED_MESSAGE
        window.dispatchEvent(new CustomEvent(SESSION_EXPIRED_EVENT, { detail: message }))
      }
    }
    return Promise.reject(error)
  },
)

/** Unwrap `{ success, message, data }` and return just `data`. */
export async function unwrap<T>(request: Promise<AxiosResponse<ApiResponse<T>>>): Promise<T> {
  const response = await request
  return response.data.data
}
