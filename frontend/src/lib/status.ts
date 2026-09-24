import type { LeadStatus } from '../api/client'

export const STATUS_LABEL: Record<LeadStatus, string> = {
  new: 'New',
  contacted: 'Contacted',
  qualified: 'Qualified',
  lost: 'Lost',
}

/** Pill colors from DESIGN.md. Always shown with the text label, never color alone. */
export const STATUS_PILL: Record<LeadStatus, string> = {
  new: 'bg-[var(--status-new-bg)] text-[var(--status-new-fg)]',
  contacted: 'bg-[var(--status-contacted-bg)] text-[var(--status-contacted-fg)]',
  qualified: 'bg-[var(--status-qualified-bg)] text-[var(--status-qualified-fg)]',
  lost: 'bg-[var(--status-lost-bg)] text-[var(--status-lost-fg)]',
}
