import { useEffect, useState } from 'react';
import { apiGet } from '../utils/api/client';

export function useNorms() {
  const [norms, setNorms] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchNorms();
  }, []);

  async function fetchNorms() {
    setIsLoading(true);
    setError(null);
    try {
      const response = await apiGet('/api/v1/norms/');
      if (response.status === 200 && Array.isArray(response.data)) {
        // Convertir API response au format Document attendu
        const converted = response.data.map((norm: any) => ({
          id: norm.id || `norm-${norm.id}`,
          title: norm.title || norm.name || 'Sans titre',
          code: norm.code || norm.id || '',
          description: norm.description || '',
          content: norm.content || norm.description || '',
          category: norm.category || 'Général',
          updatedAt: norm.updated_at || new Date().toISOString(),
          updatedBy: norm.updated_by || 'Admin',
          updatedByEmail: norm.updated_by_email || 'admin@cnetp.cd',
          references: norm.references || [],
          driveFolderUrl: norm.drive_folder_url || '',
          meetMeetingUrl: norm.meet_meeting_url || ''
        }));
        setNorms(converted);
      } else {
        setError('Impossible de charger les normes');
      }
    } catch (err) {
      console.error('Error fetching norms:', err);
      setError('Erreur lors du chargement des normes');
    } finally {
      setIsLoading(false);
    }
  }

  return { norms, isLoading, error, refetch: fetchNorms };
}

export function useExperts() {
  const [experts, setExperts] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchExperts();
  }, []);

  async function fetchExperts() {
    setIsLoading(true);
    setError(null);
    try {
      const response = await apiGet('/api/v1/experts/');
      if (response.status === 200 && Array.isArray(response.data)) {
        // Convertir API response au format Collaborator/Expert attendu
        const converted = response.data.map((expert: any) => ({
          id: expert.id || `exp-${expert.id}`,
          name: expert.first_name && expert.last_name 
            ? `${expert.first_name} ${expert.last_name}`
            : expert.username || 'Expert',
          email: expert.email || '',
          structure: expert.structure || '',
          role: expert.role_label || expert.role || 'Expert',
          phone: expert.phone || '',
          isApproved: expert.is_approved !== false,
          avatarColor: generateAvatarColor(expert.id || expert.username)
        }));
        setExperts(converted);
      } else {
        setError('Impossible de charger les experts');
      }
    } catch (err) {
      console.error('Error fetching experts:', err);
      setError('Erreur lors du chargement des experts');
    } finally {
      setIsLoading(false);
    }
  }

  return { experts, isLoading, error, refetch: fetchExperts };
}

function generateAvatarColor(seed: string): string {
  const colors = [
    '#10b981', // emerald
    '#3b82f6', // blue
    '#f59e0b', // amber
    '#ef4444', // red
    '#8b5cf6', // purple
    '#06b6d4', // cyan
  ];
  const hash = seed.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0);
  return colors[hash % colors.length];
}
