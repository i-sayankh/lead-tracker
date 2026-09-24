import { secondaryButton } from './buttons'

interface Props {
  page: number
  pageSize: number
  total: number
  onPageChange: (page: number) => void
}

export function Pagination({ page, pageSize, total, onPageChange }: Props) {
  const first = (page - 1) * pageSize + 1
  const last = Math.min(page * pageSize, total)
  return (
    <nav aria-label="Pagination" className="flex items-center justify-between gap-4">
      <p className="text-body-sm text-ink-subtle tabular-nums" aria-live="polite">
        Showing <span className="text-ink">{first}</span>–<span className="text-ink">{last}</span>{' '}
        of <span className="text-ink">{total}</span>
      </p>
      <div className="flex gap-2">
        <button
          type="button"
          className={secondaryButton}
          disabled={page <= 1}
          onClick={() => onPageChange(page - 1)}
        >
          Previous
        </button>
        <button
          type="button"
          className={secondaryButton}
          disabled={last >= total}
          onClick={() => onPageChange(page + 1)}
        >
          Next
        </button>
      </div>
    </nav>
  )
}
