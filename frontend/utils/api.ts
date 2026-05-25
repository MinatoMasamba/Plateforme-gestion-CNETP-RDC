import axios from 'axios';

// Utiliser l'URL de base de l'API si elle est définie dans l'environnement, 
// sinon pointer vers l'hôte local par défaut (à configurer quand le backend Django sera lancé)
export const API_BASE_URL = (import.meta as any).env?.VITE_API_BASE_URL || 'http://localhost:8000/api';

/**
 * Client Axios configuré pour communiquer avec le backend Django de la plateforme :
 * https://github.com/MinatoMasamba/Plateforme-gestion-CNETP-RDC.git
 */
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  // Pour le support des sessions CSRF de Django :
  withCredentials: true,
});

// Intercepteur pour inclure dynamiquement le jeton d'authentification (si utilisé)
apiClient.interceptors.request.use(
  (config) => {
    // Si JWT est utilisé au lieu des sessions par défaut, récupérer le jeton
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

/**
 * Service API pour centraliser tous les appels vers le backend Django.
 */
export const ApiService = {
  // Exemples d'appels API 
  
  auth: {
    login: (credentials: any) => apiClient.post('/auth/login/', credentials),
    logout: () => apiClient.post('/auth/logout/'),
    getProfile: () => apiClient.get('/auth/me/'),
  },

  documents: {
    getAll: () => apiClient.get('/documents/'),
    getById: (id: string) => apiClient.get(`/documents/${id}/`),
    create: (data: any) => apiClient.post('/documents/', data),
    update: (id: string, data: any) => apiClient.put(`/documents/${id}/`, data),
  },

  experts: {
    getAll: () => apiClient.get('/experts/'),
    getById: (id: string) => apiClient.get(`/experts/${id}/`),
  },

  meetings: {
    getAll: () => apiClient.get('/meetings/'),
    create: (data: any) => apiClient.post('/meetings/', data),
  },
  
  votes: {
    castVote: (data: any) => apiClient.post('/votes/cast/', data),
    getResults: (meetingId: string) => apiClient.get(`/votes/results/${meetingId}/`),
  }
};

export default ApiService;
