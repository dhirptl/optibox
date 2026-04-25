import { useState } from "react";

export type RightPanelTab = "pallets" | "events";

export function useRightPanelTab() {
  const [tab, setTab] = useState<RightPanelTab>("pallets");
  return { tab, setTab };
}
