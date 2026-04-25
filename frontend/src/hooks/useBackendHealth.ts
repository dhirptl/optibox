import { useEffect, useState } from 'react'
import { healthCheck } from '../lib/api'

export function useBackendHealth() {
  const [isHealthy, setIsHealthy] = useState(true)

  useEffect(() => {
    let mounted = true

    async function check() {
      const ok = await healthCheck()
      if (mounted) setIsHealthy(ok)
    }

    check()
    const timer = window.setInterval(check, 5000)

    return () => {
      mounted = false
      window.clearInterval(timer)
    }
  }, [])

  return isHealthy
}
