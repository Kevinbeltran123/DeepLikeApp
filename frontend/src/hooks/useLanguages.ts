import { useEffect, useState } from 'react';
import { fetchLanguages } from '../services/translationApi';

export const useLanguages = () => {
  const [languages, setLanguages] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchLanguages()
      .then(setLanguages)
      .catch((err: unknown) => setError(err instanceof Error ? err.message : 'Unknown error'))
      .finally(() => setLoading(false));
  }, []);

  return { languages, loading, error };
};
