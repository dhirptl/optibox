import { useCallback, useState } from 'react'
import { fetchSiloState } from '../lib/api'
import type { SiloState } from '../lib/types'

export function useSiloState() {
  const [silo, setSilo] = useState<SiloState>(new Map())

  const refetch = useCallback(async (csvPath?: string) => {
    const next = await fetchSiloState(csvPath)
    setSilo(next)
    return next
  }, [])

  return { silo, setSilo, refetch }
}
