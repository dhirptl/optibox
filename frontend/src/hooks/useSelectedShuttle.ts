import { useCallback, useState } from "react";

export function useSelectedShuttle() {
  const [selectedShuttle, setSelectedShuttle] = useState<number | null>(null);
  const selectShuttle = useCallback(
    (id: number) => setSelectedShuttle(id),
    [],
  );
  const clearShuttle = useCallback(() => setSelectedShuttle(null), []);
  return { selectedShuttle, selectShuttle, clearShuttle };
}
