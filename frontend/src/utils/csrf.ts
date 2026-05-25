/**
 * CSRF Token Utility
 * Reads the CSRF token injected by Django into window.__INITIAL_STATE__
 * and provides helper functions to include it in API requests
 */

interface InitialState {
  csrfToken?: string;
  user?: any;
  apiBase?: string;
  config?: any;
  stats?: any;
}

/**
 * Get the CSRF token from the initial state injected by Django
 */
export function getCSRFToken(): string {
  const initialState = (window as any).__INITIAL_STATE__ as InitialState | undefined;
  return initialState?.csrfToken || '';
}

/**
 * Get the full initial state from Django
 */
export function getInitialState(): InitialState {
  return (window as any).__INITIAL_STATE__ as InitialState || {};
}

/**
 * Get the current authenticated user from initial state
 */
export function getCurrentUser() {
  const initialState = getInitialState();
  return initialState.user || null;
}

/**
 * Get the API base URL
 */
export function getApiBase(): string {
  const initialState = getInitialState();
  return initialState.apiBase || '/api/v1/';
}

/**
 * Add CSRF token to request headers
 * Used for POST, PUT, PATCH, DELETE requests
 */
export function getCSRFHeaders(): { 'X-CSRFToken': string } {
  return {
    'X-CSRFToken': getCSRFToken(),
  };
}

/**
 * Check if a request method needs CSRF token
 */
export function methodNeedsCSRF(method: string): boolean {
  const safeMethod = method.toUpperCase();
  return !['GET', 'HEAD', 'OPTIONS'].includes(safeMethod);
}

/**
 * Create axios request config with CSRF token for unsafe methods
 */
export function createRequestConfig(method: string = 'GET', additionalConfig: any = {}) {
  const config: any = {
    method,
    ...additionalConfig,
  };

  if (methodNeedsCSRF(method)) {
    config.headers = {
      ...config.headers,
      ...getCSRFHeaders(),
      'Content-Type': 'application/json',
    };
  }

  return config;
}
