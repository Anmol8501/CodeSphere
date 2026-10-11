import type { ApiResponse } from '../types/api'
import type { LoginCredentials, LoginPortal, RegisterPayload, TokenData, User } from '../types/auth'
import { api, unwrap } from './api'

export const authService = {
  register(payload: RegisterPayload): Promise<User> {
    return unwrap(api.post<ApiResponse<User>>('/auth/register', payload))
  },

  login(credentials: LoginCredentials, portal: LoginPortal): Promise<TokenData> {
    return unwrap(api.post<ApiResponse<TokenData>>('/auth/login', { ...credentials, portal }))
  },

  me(): Promise<User> {
    return unwrap(api.get<ApiResponse<User>>('/auth/me'))
  },

  async logout(): Promise<void> {
    await api.post('/auth/logout')
  },
}
