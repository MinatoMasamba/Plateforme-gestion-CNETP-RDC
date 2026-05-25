/**
 * API Client Utility
 * Configures axios with CSRF token interceptor
 * All POST, PUT, PATCH, DELETE requests automatically include CSRF token
 */

import axios from 'axios';
import { getCSRFToken, getApiBase, methodNeedsCSRF } from '../csrf';

/**
 * Create axios instance with CSRF interceptor
 */
const apiClient = axios.create({
  baseURL: getApiBase(),
  withCredentials: true, // Include cookies (Django session)
});

/**
 * Request interceptor: Add CSRF token to unsafe methods
 */
apiClient.interceptors.request.use(
  (config) => {
    // Only add CSRF token for non-GET requests
    if (methodNeedsCSRF(config.method || 'GET')) {
      config.headers['X-CSRFToken'] = getCSRFToken();
    }

    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

/**
 * Response interceptor: Handle common errors
 */
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    // Handle 403 CSRF token errors
    if (error.response?.status === 403 && error.response?.statusText?.includes('CSRF')) {
      console.error('CSRF token validation failed. Please refresh the page.');
      window.location.reload();
    }

    // Handle 401 unauthorized
    if (error.response?.status === 401) {
      console.error('Unauthorized. Please log in again.');
      window.location.href = '/auth/login/';
    }

    return Promise.reject(error);
  }
);

/**
 * GET request helper
 */
export const apiGet = (url: string, config = {}) =>
  apiClient.get(url, config);

/**
 * POST request helper
 */
export const apiPost = (url: string, data: any = {}, config = {}) =>
  apiClient.post(url, data, config);

/**
 * PUT request helper
 */
export const apiPut = (url: string, data: any = {}, config = {}) =>
  apiClient.put(url, data, config);

/**
 * PATCH request helper
 */
export const apiPatch = (url: string, data: any = {}, config = {}) =>
  apiClient.patch(url, data, config);

/**
 * DELETE request helper
 */
export const apiDelete = (url: string, config = {}) =>
  apiClient.delete(url, config);

export default apiClient;
