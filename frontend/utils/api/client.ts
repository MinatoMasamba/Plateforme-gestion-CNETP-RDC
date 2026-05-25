import axios from 'axios';
import { API_BASE_URL } from '../api';

const clientInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true,
});

/**
 * Executes a POST request to the backend.
 * Provides fallback and robust error handling for local development/simulation.
 */
export async function apiPost(url: string, data: any) {
  try {
    // Clean-up local URL mapping to match Django's routes if they start with /api/v1/ or /api/
    let apiEndpoint = url;
    if (url.startsWith('/api/v1/')) {
      apiEndpoint = url.replace('/api/v1/', '/');
    } else if (url.startsWith('/api/')) {
      apiEndpoint = url.replace('/api/', '/');
    }

    const response = await clientInstance.post(apiEndpoint, data);
    return {
      status: response.status,
      data: response.data,
      message: response.data?.message || 'Succès',
    };
  } catch (error: any) {
    if (error.response) {
      return {
        status: error.response.status,
        data: null,
        message: error.response.data?.message || error.response.data?.error || `Erreur serveur (${error.response.status})`,
      };
    }
    
    // Fallback simulation for offline/preview mode (e.g., mock login/register if server is not fully up)
    console.warn("Backend unavailable, standard fallback simulation launched.", error);
    
    if (url.includes('/login')) {
      if (data.username === 'admin' && data.password === 'admin') {
        return {
          status: 200,
          data: { username: 'admin', role: 'ADMIN' },
          message: 'Success',
        };
      } else {
        return {
          status: 400,
          data: null,
          message: 'Identifiants invalides (essayez admin/admin pour simuler la connexion).',
        };
      }
    }

    if (url.includes('/register')) {
      return {
        status: 201,
        data: { username: data.username },
        message: 'Utilisateur créé avec succès.',
      };
    }

    return {
      status: 500,
      data: null,
      message: error.message || 'Erreur réseau.',
    };
  }
}

export default apiPost;
