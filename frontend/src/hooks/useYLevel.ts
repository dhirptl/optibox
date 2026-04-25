import { useState } from "react";

export function useYLevel() {
  const [y, setY] = useState<number>(1);
  return { y, setY };
}
