import { createContext } from 'react'
import type { LoginCredentials, LoginPortal, RegisterPayload, User } from '../types/auth'

export interface AuthContextValue {
  user: User | null
  isAuthenticated: boolean
  /** True while the stored token is being checked on first load. */
  loading: boolean
  login: (credentials: LoginCredentials, portal: LoginPortal) => Promise<User>
  register: (payload: RegisterPayload) => Promise<User>
  logout: () => Promise<void>
  refreshUser: () => Promise<User | null>
}

export const AuthContext = createContext<AuthContextValue | undefined>(undefined)
