import { useEffect, useState } from "react";
import { healthCheck } from "../lib/api";

export function useBackendHealth() {
  const [healthy, setHealthy] = useState<boolean | null>(null);

  useEffect(() => {
    let alive = true;
    const check = async () => {
      const ok = await healthCheck();
      if (alive) setHealthy(ok);
    };
    check();
    const id = setInterval(check, 5000);
    return () => {
      alive = false;
      clearInterval(id);
    };
  }, []);

  return healthy;
}
