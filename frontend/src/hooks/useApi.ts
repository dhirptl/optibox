import { useCallback, useState } from "react";

export function useApi<T, A extends unknown[]>(fn: (...args: A) => Promise<T>) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const call = useCallback(
    async (...args: A): Promise<T | undefined> => {
      setLoading(true);
      setError(null);
      try {
        return await fn(...args);
      } catch (e) {
        setError(e instanceof Error ? e.message : String(e));
        return undefined;
      } finally {
        setLoading(false);
      }
    },
    [fn],
  );

  return { call, loading, error };
}
