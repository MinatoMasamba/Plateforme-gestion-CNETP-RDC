import { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { apiGet, apiPost } from '../utils/api/client';

export interface User {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  phone?: string;
  is_expert?: boolean;
  is_ctc_staff?: boolean;
  is_minister?: boolean;
  structure?: string;
}

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  login: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  register: (userData: any) => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    checkAuth();
  }, []);

  async function checkAuth() {
    setIsLoading(true);
    try {
      const response = await apiGet('/api/v1/auth/me/');
      if (response.status === 200 && response.data) {
        setUser(response.data);
        setError(null);
      } else {
        setUser(null);
      }
    } catch (err) {
      console.error('Auth check error:', err);
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  }

  async function login(username: string, password: string) {
    setIsLoading(true);
    setError(null);
    try {
      const response = await apiPost('/api/v1/auth/login/', { username, password });
      
      if (response.status === 200 && response.data?.user) {
        setUser(response.data.user);
        await new Promise(r => setTimeout(r, 100));
      } else {
        // Propagate the actual error response from the backend
        const errorToThrow = new Error(response.message || 'Login failed');
        (errorToThrow as any).data = response.data; // Attach backend data to the error
        throw errorToThrow;
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Login failed';
      setError(message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }

  async function logout() {
    setIsLoading(true);
    try {
      await apiPost('/api/v1/auth/logout/', {});
      setUser(null);
      setError(null);
    } catch (err) {
      console.error('Logout error:', err);
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  }

  async function register(userData: any) {
    setIsLoading(true);
    setError(null);
    try {
      const response = await apiPost('/api/v1/auth/register/', userData);
      if (response.status === 201) {
        return;
      } else {
        throw new Error(response.message || 'Registration failed');
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Registration failed';
      setError(message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        isLoading,
        error,
        login,
        logout,
        register,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
}
