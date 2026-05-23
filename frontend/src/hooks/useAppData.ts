import { useState, useEffect } from 'react';

/**
 * Custom hook to fetch application data from Django API
 * Handles mock data while real backend is being integrated
 */

export interface UseAppDataResult {
  documents: any[];
  collaborators: any[];
  experts: any[];
  workingGroups: any[];
  meetings: any[];
  votes: any[];
  financial: any;
  validation: any;
  legistique: any;
  versions: any[];
  isLoading: boolean;
  error: string | null;
  refetch: () => void;
}

export const useAppData = (): UseAppDataResult => {
  const [documents, setDocuments] = useState<any[]>([]);
  const [collaborators, setCollaborators] = useState<any[]>([]);
  const [experts, setExperts] = useState<any[]>([]);
  const [workingGroups, setWorkingGroups] = useState<any[]>([]);
  const [meetings, setMeetings] = useState<any[]>([]);
  const [votes, setVotes] = useState<any[]>([]);
  const [financial, setFinancial] = useState<any>({});
  const [validation, setValidation] = useState<any>({});
  const [legistique, setLegistique] = useState<any>({});
  const [versions, setVersions] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await fetch('/api/app-data/');
      
      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }
      
      const json = await response.json();
      
      if (json.status === 'success' && json.data) {
        setDocuments(json.data.documents || []);
        setCollaborators(json.data.collaborators || []);
        setExperts(json.data.experts || []);
        setWorkingGroups(json.data.workingGroups || []);
        setMeetings(json.data.meetings || []);
        setVotes(json.data.votes || []);
        setFinancial(json.data.financial || {});
        setValidation(json.data.validation || {});
        setLegistique(json.data.legistique || {});
        setVersions(json.data.versions || []);
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Unknown error';
      setError(message);
      console.error('Failed to fetch app data:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  return {
    documents,
    collaborators,
    experts,
    workingGroups,
    meetings,
    votes,
    financial,
    validation,
    legistique,
    versions,
    isLoading,
    error,
    refetch: fetchData
  };
};

/**
 * Fetch individual resource from API
 */
export const fetchAppResource = async (resource: string): Promise<any[]> => {
  try {
    const response = await fetch(`/api/${resource}/`);
    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }
    const json = await response.json();
    return json.data || [];
  } catch (err) {
    console.error(`Failed to fetch ${resource}:`, err);
    return [];
  }
};
