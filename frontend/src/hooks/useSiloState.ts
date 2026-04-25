import { useCallback, useEffect, useState } from "react";
import { fetchSiloState } from "../lib/api";
import type { SiloState } from "../lib/types";

export function useSiloState() {
  const [silo, setSilo] = useState<SiloState>(new Map());
  const [error, setError] = useState<string | null>(null);

  const refetch = useCallback(async () => {
    try {
      const next = await fetchSiloState();
      setSilo(next);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }, []);

  useEffect(() => {
    refetch();
  }, [refetch]);

  return { silo, error, refetch };
}
