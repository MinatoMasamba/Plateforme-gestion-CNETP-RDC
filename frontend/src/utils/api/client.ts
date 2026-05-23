/**
 * Django API Client
 * Wrapper fetch avec CSRF + session automatique
 */

import { getCsrfToken, setCsrfHeader } from './django-csrf'

interface DjangoFetchOptions extends RequestInit {
  csrfToken?: string
}

interface ApiResponse<T = any> {
  data?: T
  status: number
  error?: string
  message?: string
}

/**
 * Wrapper fetch pour Django avec CSRF protection
 */
export async function djangoFetch<T = any>(
  url: string,
  options: DjangoFetchOptions = {}
): Promise<ApiResponse<T>> {
  const method = (options.method || 'GET').toUpperCase()
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...options.headers,
  } as Record<string, string>

  // Ajouter CSRF token pour POST/PUT/DELETE/PATCH
  if (['POST', 'PUT', 'DELETE', 'PATCH'].includes(method)) {
    setCsrfHeader(headers)
  }

  try {
    const response = await fetch(url, {
      ...options,
      method,
      headers,
      // Les credentials inclus les cookies (sessionid)
      credentials: 'same-origin',
    })

    const contentType = response.headers.get('content-type')
    let data: any = null

    if (contentType && contentType.includes('application/json')) {
      data = await response.json()
    } else {
      data = await response.text()
    }

    // Gestion des erreurs d'authentification
    if (response.status === 401) {
      console.warn('Session expirée - redirection vers login')
      // Rediriger vers la page de login
      window.location.href = '/auth/login/'
    }

    return {
      data,
      status: response.status,
      error: response.ok ? undefined : data?.error || data?.detail,
      message: data?.message || data?.detail,
    }
  } catch (error) {
    console.error('API Error:', error)
    return {
      status: 0,
      error: error instanceof Error ? error.message : 'Unknown error',
    }
  }
}

/**
 * GET request
 */
export function apiGet<T = any>(
  url: string,
  options?: Omit<DjangoFetchOptions, 'method'>
): Promise<ApiResponse<T>> {
  return djangoFetch<T>(url, {
    ...options,
    method: 'GET',
  })
}

/**
 * POST request
 */
export function apiPost<T = any>(
  url: string,
  data?: any,
  options?: Omit<DjangoFetchOptions, 'method' | 'body'>
): Promise<ApiResponse<T>> {
  return djangoFetch<T>(url, {
    ...options,
    method: 'POST',
    body: data ? JSON.stringify(data) : undefined,
  })
}

/**
 * PUT request
 */
export function apiPut<T = any>(
  url: string,
  data?: any,
  options?: Omit<DjangoFetchOptions, 'method' | 'body'>
): Promise<ApiResponse<T>> {
  return djangoFetch<T>(url, {
    ...options,
    method: 'PUT',
    body: data ? JSON.stringify(data) : undefined,
  })
}

/**
 * PATCH request
 */
export function apiPatch<T = any>(
  url: string,
  data?: any,
  options?: Omit<DjangoFetchOptions, 'method' | 'body'>
): Promise<ApiResponse<T>> {
  return djangoFetch<T>(url, {
    ...options,
    method: 'PATCH',
    body: data ? JSON.stringify(data) : undefined,
  })
}

/**
 * DELETE request
 */
export function apiDelete<T = any>(
  url: string,
  options?: Omit<DjangoFetchOptions, 'method'>
): Promise<ApiResponse<T>> {
  return djangoFetch<T>(url, {
    ...options,
    method: 'DELETE',
  })
}
