export type Role = 'STUDENT' | 'STAFF' | 'ADMIN'

/** Which login screen the user signed in from. Sent to the backend, which verifies it. */
export type LoginPortal = Role

export interface User {
  id: number
  full_name: string
  email: string
  role: Role
  is_active: boolean
  created_at: string
}

export interface LoginCredentials {
  email: string
  password: string
}

export interface RegisterPayload {
  full_name: string
  email: string
  password: string
  confirm_password: string
}

export interface TokenData {
  access_token: string
  token_type: 'bearer'
  expires_in: number
  user: User
}
