import { useContext } from 'react'
import { AuthContext, type AuthContextValue } from '../context/authContextValue'

/** Access the current user and auth actions: `const { user, login, logout } = useAuth()`. */
export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext)
  if (!context) throw new Error('useAuth must be used inside <AuthProvider>')
  return context
}
