import { useCallback, useState } from 'react'
import { LEAD_STATUSES, type LeadStatus } from '../api/client'
import { PAGE_SIZE } from './useLeads'

// The API caps offset at 1,000,000 (backend MAX_OFFSET); later pages would only return 422.
const MAX_PAGE = Math.floor(1_000_000 / PAGE_SIZE) + 1

interface ListState {
  q: string
  status: LeadStatus | null
  page: number
}

function isLeadStatus(value: string | null): value is LeadStatus {
  return LEAD_STATUSES.some((s) => s === value)
}

function readUrl(): ListState {
  const params = new URLSearchParams(window.location.search)
  const status = params.get('status')
  const page = Number.parseInt(params.get('page') ?? '', 10)
  return {
    q: params.get('q') ?? '',
    status: isLeadStatus(status) ? status : null,
    page: Number.isInteger(page) && page > 0 && page <= MAX_PAGE ? page : 1,
  }
}

function writeUrl(state: ListState): void {
  const params = new URLSearchParams()
  if (state.q) params.set('q', state.q)
  if (state.status) params.set('status', state.status)
  if (state.page > 1) params.set('page', String(state.page))
  const qs = params.toString()
  window.history.replaceState(null, '', `${window.location.pathname}${qs ? `?${qs}` : ''}`)
}

/** Search, status filter and page live in the URL so views are shareable and survive a refresh. */
export function useUrlState(): [ListState, (patch: Partial<ListState>) => void] {
  const [state, setState] = useState(readUrl)
  const update = useCallback((patch: Partial<ListState>) => {
    setState((prev) => {
      const next = { ...prev, ...patch }
      writeUrl(next)
      return next
    })
  }, [])
  return [state, update]
}
