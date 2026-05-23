/**
 * Hook React pour gérer l'authentification Django
 */

import { useState, useEffect } from 'react'
import { apiGet } from '../api/client'

export interface User {
  id: number
  email: string
  first_name: string
  last_name: string
  full_name: string
  is_expert: boolean
  is_staff: boolean
  is_active: boolean
  roles?: string[]
  ctm?: {
    id: number
    titre: string
  }
  wgs?: Array<{
    id: number
    titre: string
  }>
}

export interface AuthState {
  isLoading: boolean
  isAuthenticated: boolean
  user: User | null
  error: string | null
}

/**
 * Hook pour récupérer l'utilisateur actuel
 */
export function useCurrentUser(): AuthState {
  const [state, setState] = useState<AuthState>({
    isLoading: true,
    isAuthenticated: false,
    user: null,
    error: null,
  })

  useEffect(() => {
    const fetchCurrentUser = async () => {
      const response = await apiGet<User>('/api/v1/auth/current-user/')
      
      if (response.status === 200 && response.data) {
        setState({
          isLoading: false,
          isAuthenticated: true,
          user: response.data,
          error: null,
        })
      } else {
        setState({
          isLoading: false,
          isAuthenticated: false,
          user: null,
          error: response.error || 'Failed to fetch user',
        })
      }
    }

    fetchCurrentUser()
  }, [])

  return state
}

/**
 * Hook pour vérifier les permissions
 */
export function usePermission(permission: string): boolean {
  const { user } = useCurrentUser()
  
  if (!user) return false

  // Les staff ont toutes les permissions
  if (user.is_staff) return true

  // Vérifier dans les rôles de l'utilisateur
  return user.roles?.includes(permission) || false
}

/**
 * Hook pour vérifier le rôle
 */
export function useRole(role: string): boolean {
  const { user } = useCurrentUser()
  return user?.roles?.includes(role) || false
}
