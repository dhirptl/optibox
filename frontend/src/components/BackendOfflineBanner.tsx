import { useState } from "react";

type Props = {
  healthy: boolean | null;
};

export function BackendOfflineBanner({ healthy }: Props) {
  const [dismissed, setDismissed] = useState(false);
  if (healthy !== false || dismissed) return null;

  return (
    <div className="bg-amber-50 border-b border-amber-200 px-6 py-2 flex items-center gap-3 text-xs text-amber-900">
      <span className="font-semibold tracking-wide">BACKEND OFFLINE</span>
      <span>
        Backend not running. Start it with:{" "}
        <code className="font-mono bg-amber-100 px-1.5 py-0.5 rounded">
          python server.py
        </code>
      </span>
      <button
        type="button"
        onClick={() => setDismissed(true)}
        aria-label="Dismiss"
        className="ml-auto text-amber-900/70 hover:text-amber-900"
      >
        ×
      </button>
    </div>
  );
}
