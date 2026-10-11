import { useCallback, useEffect, useState } from 'react'
import { getErrorMessage } from '../utils/errors'

interface QueryState<T> {
  data: T | null
  error: string | null
  loading: boolean
  reload: () => void
}

/**
 * Minimal data-fetching hook. Runs `fetcher` on mount and whenever the
 * `fetcher` function changes, ignoring results from outdated requests.
 *
 * Pass a stable function (module-level, or wrapped in useCallback with the
 * values it depends on) so it doesn't refetch on every render.
 */
export function useApiQuery<T>(fetcher: () => Promise<T>): QueryState<T> {
  const [data, setData] = useState<T | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [reloadKey, setReloadKey] = useState(0)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError(null)
    fetcher()
      .then((result) => {
        if (!cancelled) setData(result)
      })
      .catch((err: unknown) => {
        if (!cancelled) setError(getErrorMessage(err))
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [fetcher, reloadKey])

  const reload = useCallback(() => setReloadKey((key) => key + 1), [])

  return { data, error, loading, reload }
}
