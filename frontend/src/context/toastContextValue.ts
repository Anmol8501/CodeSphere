import { createContext } from 'react'

export type ToastVariant = 'success' | 'error' | 'info' | 'warning'

export interface ToastOptions {
  variant?: ToastVariant
  /** Milliseconds; 0 keeps the toast until dismissed. */
  duration?: number
}

export interface ToastContextValue {
  toast: (message: string, options?: ToastOptions) => void
}

export const ToastContext = createContext<ToastContextValue | null>(null)
