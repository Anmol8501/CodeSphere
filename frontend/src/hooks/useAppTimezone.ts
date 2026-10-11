import { useEffect, useState } from 'react'
import { getAppTimezone } from '../services/appTimezone'

/** The server's application timezone, or null while it is being fetched. */
export function useAppTimezone(): string | null {
  const [timezone, setTimezone] = useState<string | null>(null)
  useEffect(() => {
    let cancelled = false
    void getAppTimezone().then((tz) => !cancelled && setTimezone(tz))
    return () => {
      cancelled = true
    }
  }, [])
  return timezone
}
