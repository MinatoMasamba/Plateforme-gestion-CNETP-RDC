import { useEffect, useState } from 'react';
import { apiGet } from '../utils/api/client';

export function useMeetings() {
  const [meetings, setMeetings] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchMeetings();
  }, []);

  async function fetchMeetings() {
    setIsLoading(true);
    setError(null);
    try {
      const response = await apiGet('/api/v1/reunions/');
      if (response.status === 200 && Array.isArray(response.data)) {
        const converted = response.data.map((meeting: any) => ({
          id: meeting.id || `meeting-${meeting.id}`,
          title: meeting.title || meeting.name || 'Sans titre',
          date: meeting.date || meeting.meeting_date || new Date().toISOString(),
          location: meeting.location || 'À déterminer',
          status: meeting.status || 'scheduled',
          description: meeting.description || '',
          participants: meeting.participants || [],
          agenda: meeting.agenda || [],
          minutes: meeting.minutes || '',
          attachments: meeting.attachments || []
        }));
        setMeetings(converted);
      } else {
        setError('Impossible de charger les réunions');
      }
    } catch (err) {
      console.error('Error fetching meetings:', err);
      setError('Erreur lors du chargement des réunions');
    } finally {
      setIsLoading(false);
    }
  }

  return { meetings, isLoading, error, refetch: fetchMeetings };
}

export function useVotes() {
  const [votes, setVotes] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchVotes();
  }, []);

  async function fetchVotes() {
    setIsLoading(true);
    setError(null);
    try {
      const response = await apiGet('/api/v1/votes/');
      if (response.status === 200 && Array.isArray(response.data)) {
        const converted = response.data.map((vote: any) => ({
          id: vote.id || `vote-${vote.id}`,
          title: vote.title || vote.subject || 'Sans titre',
          description: vote.description || '',
          status: vote.status || 'open',
          votedBy: vote.voted_by || vote.votes || [],
          createdAt: vote.created_at || new Date().toISOString(),
          dueDate: vote.due_date || new Date(Date.now() + 7*24*60*60*1000).toISOString(),
          options: vote.options || [],
          results: vote.results || {}
        }));
        setVotes(converted);
      } else {
        setError('Impossible de charger les votes');
      }
    } catch (err) {
      console.error('Error fetching votes:', err);
      setError('Erreur lors du chargement des votes');
    } finally {
      setIsLoading(false);
    }
  }

  return { votes, isLoading, error, refetch: fetchVotes };
}

export function usePayments() {
  const [payments, setPayments] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchPayments();
  }, []);

  async function fetchPayments() {
    setIsLoading(true);
    setError(null);
    try {
      const response = await apiGet('/api/v1/paiements/');
      if (response.status === 200 && Array.isArray(response.data)) {
        const converted = response.data.map((payment: any) => ({
          id: payment.id || `payment-${payment.id}`,
          expert: payment.expert || payment.expert_name || 'Inconnu',
          amount: payment.amount || 0,
          type: payment.type || payment.payment_type || 'honoraire',
          date: payment.date || payment.payment_date || new Date().toISOString(),
          status: payment.status || 'pending',
          method: payment.method || payment.payment_method || 'bank_transfer',
          reference: payment.reference || payment.reference_number || '',
          notes: payment.notes || ''
        }));
        setPayments(converted);
      } else {
        setError('Impossible de charger les paiements');
      }
    } catch (err) {
      console.error('Error fetching payments:', err);
      setError('Erreur lors du chargement des paiements');
    } finally {
      setIsLoading(false);
    }
  }

  return { payments, isLoading, error, refetch: fetchPayments };
}
