import { useEffect, useState } from 'react'
import { EmptyState } from './components/EmptyState'
import { LeadForm } from './components/LeadForm'
import { LeadTable, LeadTableSkeleton } from './components/LeadTable'
import { Pagination } from './components/Pagination'
import { StatusSelect } from './components/StatusSelect'
import { Toasts } from './components/Toasts'
import { Toolbar } from './components/Toolbar'
import { primaryButton, secondaryButton } from './components/buttons'
import { useDebouncedValue } from './hooks/useDebouncedValue'
import { PAGE_SIZE, useLeads } from './hooks/useLeads'
import { useToasts } from './hooks/useToasts'
import { useUrlState } from './hooks/useUrlState'
import { STATUS_LABEL } from './lib/status'

export const SEARCH_DEBOUNCE_MS = 300

export default function App() {
  const [view, setView] = useUrlState()
  const [createOpen, setCreateOpen] = useState(false)
  const { toasts, push: toast, dismiss } = useToasts()
  const debouncedQ = useDebouncedValue(view.q, SEARCH_DEBOUNCE_MS)
  const { data, error, loading, slow, reload, replaceLead } = useLeads({
    q: debouncedQ,
    status: view.status,
    page: view.page,
  })

  // A shared link or a shrinking result set can point past the last page.
  useEffect(() => {
    if (data && data.items.length === 0 && data.total > 0 && view.page > 1) {
      setView({ page: Math.ceil(data.total / PAGE_SIZE) })
    }
  }, [data, view.page, setView])

  const hasFilters = Boolean(debouncedQ.trim() || view.status)
  const clearFilters = () => setView({ q: '', status: null, page: 1 })
  const openCreate = () => setCreateOpen(true)

  let content
  if (error && !data) {
    content = (
      <EmptyState
        tone="error"
        title="Couldn't load leads"
        description={error.message}
        action={
          <button type="button" className={secondaryButton} onClick={reload}>
            Retry
          </button>
        }
      />
    )
  } else if (!data) {
    content = <LeadTableSkeleton />
  } else if (data.total === 0 && !hasFilters) {
    content = (
      <EmptyState
        title="No leads yet"
        description="Leads you add will show up here, newest first."
        action={
          <button type="button" className={primaryButton} onClick={openCreate}>
            Create your first lead
          </button>
        }
      />
    )
  } else if (data.total === 0) {
    const term = debouncedQ.trim()
    const noun = view.status ? `${STATUS_LABEL[view.status].toLowerCase()} leads` : 'leads'
    content = (
      <EmptyState
        title={term ? `No ${noun} match “${term}”` : `No ${noun} yet`}
        action={
          <button type="button" className={secondaryButton} onClick={clearFilters}>
            Clear filters
          </button>
        }
      />
    )
  } else {
    content = (
      <div className="flex flex-col gap-4">
        <div className={loading ? 'opacity-60 transition-opacity' : 'transition-opacity'}>
          <LeadTable
            leads={data.items}
            renderStatus={(lead) => (
              <StatusSelect
                lead={lead}
                onUpdated={replaceLead}
                onError={(message) => toast(message, 'error')}
              />
            )}
          />
        </div>
        <Pagination
          page={view.page}
          pageSize={PAGE_SIZE}
          total={data.total}
          onPageChange={(page) => setView({ page })}
        />
      </div>
    )
  }

  return (
    <div className="mx-auto flex max-w-6xl flex-col gap-6 px-4 py-8 sm:px-6">
      <a
        href="#leads"
        className="sr-only rounded-md bg-primary px-3 py-2 text-body-sm text-on-primary focus:not-sr-only focus:fixed focus:top-2 focus:left-2 focus:z-50"
      >
        Skip to leads
      </a>
      <header className="flex items-center justify-between gap-4">
        <div>
          <h1 className="text-headline font-semibold text-balance">Leads</h1>
          {data && (
            <p className="text-body-sm text-ink-subtle tabular-nums">
              {data.total} {data.total === 1 ? 'lead' : 'leads'}
              {hasFilters ? ' matching' : ''}
            </p>
          )}
        </div>
        <button type="button" className={primaryButton} onClick={openCreate}>
          New lead
        </button>
      </header>

      <Toolbar
        q={view.q}
        status={view.status}
        onSearchChange={(q) => setView({ q, page: 1 })}
        onStatusChange={(status) => setView({ status, page: 1 })}
      />

      {slow && (
        <p
          role="status"
          className="rounded-md border border-hairline bg-surface-1 px-4 py-3 text-body-sm text-ink-muted"
        >
          Waking up the server — the free tier sleeps when idle (up to ~50s)…
        </p>
      )}
      {error && data && (
        <p role="alert" className="text-body-sm text-danger">
          {error.message}{' '}
          <button type="button" className="font-medium underline" onClick={reload}>
            Retry
          </button>
        </p>
      )}

      <main id="leads" tabIndex={-1} className="focus:outline-none">
        {content}
      </main>

      <LeadForm
        open={createOpen}
        onClose={() => setCreateOpen(false)}
        onCreated={() => {
          setCreateOpen(false)
          toast('Lead created')
          // Newest first, so the new lead is at the top of page 1 of the unfiltered list.
          setView({ page: 1 })
          reload()
        }}
      />
      <Toasts toasts={toasts} onDismiss={dismiss} />
    </div>
  )
}
