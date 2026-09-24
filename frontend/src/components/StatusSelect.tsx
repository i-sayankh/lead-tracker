import { useState } from 'react'
import {
  ApiError,
  LEAD_STATUSES,
  updateLeadStatus,
  type Lead,
  type LeadStatus,
} from '../api/client'
import { STATUS_LABEL, STATUS_PILL } from '../lib/status'

interface Props {
  lead: Lead
  onUpdated: (lead: Lead) => void
  onError: (message: string) => void
}

/** Native select styled as a status pill. Changes apply optimistically and roll back on failure. */
export function StatusSelect({ lead, onUpdated, onError }: Props) {
  const [optimistic, setOptimistic] = useState<LeadStatus | null>(null)
  const shown = optimistic ?? lead.status
  const pending = optimistic !== null

  async function change(next: LeadStatus) {
    if (next === lead.status) return
    setOptimistic(next)
    try {
      onUpdated(await updateLeadStatus(lead.id, next))
    } catch (err) {
      const reason = err instanceof ApiError ? err.message : 'Please try again.'
      onError(`Couldn't update ${lead.name} to ${STATUS_LABEL[next]}. ${reason}`)
    } finally {
      // On success the parent now holds the new status; on failure this is the rollback.
      setOptimistic(null)
    }
  }

  return (
    <div className={`relative inline-flex rounded-full ${STATUS_PILL[shown]}`}>
      <select
        aria-label={`Status for ${lead.name}`}
        value={shown}
        disabled={pending}
        aria-busy={pending || undefined}
        onChange={(e) => {
          const next = LEAD_STATUSES.find((s) => s === e.target.value)
          if (next) void change(next)
        }}
        className="h-10 cursor-pointer appearance-none rounded-full border border-transparent bg-transparent pr-7 pl-3 text-caption font-medium text-inherit transition-opacity duration-150 hover:border-hairline-strong disabled:cursor-progress disabled:opacity-70"
      >
        {LEAD_STATUSES.map((s) => (
          <option key={s} value={s} className="bg-canvas text-ink">
            {STATUS_LABEL[s]}
          </option>
        ))}
      </select>
      <svg
        aria-hidden="true"
        viewBox="0 0 16 16"
        className="pointer-events-none absolute top-1/2 right-2.5 size-3 -translate-y-1/2"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
      >
        <path d="M4 6l4 4 4-4" />
      </svg>
    </div>
  )
}
