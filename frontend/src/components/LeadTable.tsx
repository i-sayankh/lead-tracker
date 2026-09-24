import type { ReactNode } from 'react'
import type { Lead } from '../api/client'
import { formatAbsolute, formatRelative } from '../lib/format'
import { STATUS_LABEL, STATUS_PILL } from '../lib/status'

interface Props {
  leads: Lead[]
  /** Renders the status cell; defaults to a read-only pill. */
  renderStatus?: (lead: Lead) => ReactNode
}

const COLUMNS = ['Name', 'Email', 'Phone', 'Status', 'Created'] as const

// Below 640px the same table restyles into stacked cards; each cell shows its column
// name via data-label so there is a single DOM for screen readers and tests.
const cell =
  'px-4 py-3 align-middle max-sm:flex max-sm:items-center max-sm:justify-between max-sm:gap-4 max-sm:px-0 max-sm:py-1 max-sm:before:text-caption max-sm:before:text-ink-subtle max-sm:before:content-[attr(data-label)]'

export function StatusPill({ status }: { status: Lead['status'] }) {
  return (
    <span
      className={`inline-flex h-6 items-center rounded-full px-2.5 text-caption font-medium ${STATUS_PILL[status]}`}
    >
      {STATUS_LABEL[status]}
    </span>
  )
}

export function LeadTable({ leads, renderStatus }: Props) {
  return (
    <table className="w-full border-collapse text-left text-body-sm max-sm:block">
      <thead className="max-sm:sr-only">
        <tr className="border-b border-hairline">
          {COLUMNS.map((c) => (
            <th key={c} scope="col" className="px-4 py-2 text-caption font-medium text-ink-subtle">
              {c}
            </th>
          ))}
        </tr>
      </thead>
      <tbody className="max-sm:flex max-sm:flex-col max-sm:gap-2">
        {leads.map((lead) => (
          <tr
            key={lead.id}
            className="border-b border-hairline max-sm:block max-sm:rounded-lg max-sm:border max-sm:bg-surface-1 max-sm:p-4"
          >
            <td data-label="Name" className={`${cell} font-medium text-ink`}>
              {lead.name}
            </td>
            <td data-label="Email" className={cell}>
              <a
                href={`mailto:${lead.email}`}
                className="break-all text-ink-muted hover:text-primary hover:underline"
              >
                {lead.email}
              </a>
            </td>
            <td data-label="Phone" className={cell}>
              <a
                href={`tel:${lead.phone}`}
                className="font-mono text-caption text-ink-muted hover:text-primary hover:underline"
              >
                {lead.phone}
              </a>
            </td>
            <td data-label="Status" className={cell}>
              {renderStatus ? renderStatus(lead) : <StatusPill status={lead.status} />}
            </td>
            <td data-label="Created" className={`${cell} whitespace-nowrap text-ink-subtle`}>
              <time dateTime={lead.created_at} title={formatAbsolute(lead.created_at)}>
                {formatRelative(lead.created_at)}
              </time>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}

export function LeadTableSkeleton({ rows = 5 }: { rows?: number }) {
  return (
    <div role="status" aria-label="Loading leads" className="flex flex-col">
      {Array.from({ length: rows }, (_, i) => (
        <div key={i} className="flex h-12 items-center gap-6 border-b border-hairline px-4">
          {['w-32', 'w-48', 'w-28', 'w-20', 'w-16'].map((w) => (
            <div key={w} className={`h-3 ${w} animate-pulse rounded-xs bg-surface-2`} />
          ))}
        </div>
      ))}
    </div>
  )
}
