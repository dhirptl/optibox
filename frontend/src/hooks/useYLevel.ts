import { useState } from 'react'

export function useYLevel() {
  const [y, setY] = useState(4)
  return { y, setY }
}
