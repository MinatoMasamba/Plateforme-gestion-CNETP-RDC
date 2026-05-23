/**
 * Django CSRF Token Handler
 * Récupère et gère le token CSRF de Django
 */

export function getCsrfToken(): string {
  // Chercher le token dans les cookies
  const name = 'csrftoken'
  let csrfToken = ''

  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';')
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim()
      if (cookie.substring(0, name.length + 1) === name + '=') {
        csrfToken = decodeURIComponent(cookie.substring(name.length + 1))
        break
      }
    }
  }

  // Fallback: chercher dans le meta tag Django
  if (!csrfToken) {
    const token = document.querySelector('meta[name="csrf-token"]')
    if (token) {
      csrfToken = token.getAttribute('content') || ''
    }
  }

  return csrfToken
}

export function setCsrfHeader(headers: Record<string, string>): Record<string, string> {
  const token = getCsrfToken()
  if (token) {
    headers['X-CSRFToken'] = token
  }
  return headers
}
