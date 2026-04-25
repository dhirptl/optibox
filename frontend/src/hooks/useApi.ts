import { useState } from 'react'
import { randomizeSilo, resetSilo } from '../lib/api'

export function useApi() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function runRandomize(numBoxes: number) {
    setLoading(true)
    setError(null)
    try {
      return await randomizeSilo(numBoxes)
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Unknown API error'
      setError(message)
      throw err
    } finally {
      setLoading(false)
    }
  }

  async function runReset() {
    setLoading(true)
    setError(null)
    try {
      return await resetSilo()
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Unknown API error'
      setError(message)
      throw err
    } finally {
      setLoading(false)
    }
  }

  return { loading, error, setError, runRandomize, runReset }
}
