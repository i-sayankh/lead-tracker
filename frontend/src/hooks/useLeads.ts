import { useCallback, useEffect, useState } from 'react'
import { ApiError, listLeads, type Lead, type LeadPage, type LeadStatus } from '../api/client'

export const PAGE_SIZE = 20
/** After this long we assume the free-tier server is cold-starting and say so. */
const SLOW_REQUEST_MS = 3000

interface Query {
  q: string
  status: LeadStatus | null
  page: number
}

export interface LeadsResult {
  /** Last successfully loaded page; kept while the next one loads. */
  data: LeadPage | null
  /** Error for the current query, if its request failed. */
  error: ApiError | null
  loading: boolean
  /** The current request has been pending for longer than SLOW_REQUEST_MS. */
  slow: boolean
  reload: () => void
  /** Swap in an updated lead without refetching (after a status change). */
  replaceLead: (lead: Lead) => void
}

export function useLeads({ q, status, page }: Query): LeadsResult {
  const [version, setVersion] = useState(0)
  const [data, setData] = useState<LeadPage | null>(null)
  // Which query the latest settled response belongs to; loading is "current query not settled".
  const [settled, setSettled] = useState<{ key: string; error: ApiError | null } | null>(null)
  const [slowKey, setSlowKey] = useState<string | null>(null)

  const key = JSON.stringify([q, status, page, version])

  useEffect(() => {
    // Abort the previous request when the query changes so a slow, stale response
    // can never overwrite a newer one.
    const controller = new AbortController()
    const slowTimer = setTimeout(() => setSlowKey(key), SLOW_REQUEST_MS)

    listLeads(
      { q: q.trim() || undefined, status, limit: PAGE_SIZE, offset: (page - 1) * PAGE_SIZE },
      controller.signal,
    )
      .then((result) => {
        setData(result)
        setSettled({ key, error: null })
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted) return
        const error =
          err instanceof ApiError
            ? err
            : new ApiError(0, 'INTERNAL_ERROR', 'Something went wrong while loading leads.')
        setSettled({ key, error })
      })
      .finally(() => clearTimeout(slowTimer))

    return () => {
      controller.abort()
      clearTimeout(slowTimer)
    }
  }, [key, q, status, page])

  const reload = useCallback(() => setVersion((v) => v + 1), [])
  const replaceLead = useCallback((lead: Lead) => {
    setData((page) =>
      page ? { ...page, items: page.items.map((l) => (l.id === lead.id ? lead : l)) } : page,
    )
  }, [])
  const loading = settled?.key !== key

  return {
    data,
    error: loading ? null : (settled?.error ?? null),
    loading,
    slow: loading && slowKey === key,
    reload,
    replaceLead,
  }
}
