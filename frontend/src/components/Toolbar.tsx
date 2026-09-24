import { useEffect, useRef } from 'react'
import { LEAD_STATUSES, type LeadStatus } from '../api/client'
import { STATUS_LABEL } from '../lib/status'

interface Props {
  q: string
  status: LeadStatus | null
  onSearchChange: (q: string) => void
  onStatusChange: (status: LeadStatus | null) => void
}

const FILTERS: { value: LeadStatus | null; label: string }[] = [
  { value: null, label: 'All' },
  ...LEAD_STATUSES.map((s) => ({ value: s, label: STATUS_LABEL[s] })),
]

function isTyping(target: EventTarget | null): boolean {
  return (
    target instanceof HTMLElement &&
    (target.isContentEditable || ['INPUT', 'TEXTAREA', 'SELECT'].includes(target.tagName))
  )
}

export function Toolbar({ q, status, onSearchChange, onStatusChange }: Props) {
  const searchRef = useRef<HTMLInputElement>(null)

  // "/" focuses search, like most data tools.
  useEffect(() => {
    function onKeyDown(event: KeyboardEvent) {
      if (event.key === '/' && !isTyping(event.target) && !event.metaKey && !event.ctrlKey) {
        event.preventDefault()
        searchRef.current?.focus()
      }
    }
    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  }, [])

  return (
    <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
      <div className="relative w-full lg:max-w-sm">
        <label htmlFor="lead-search" className="sr-only">
          Search leads
        </label>
        <input
          ref={searchRef}
          id="lead-search"
          name="q"
          type="search"
          value={q}
          onChange={(e) => onSearchChange(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Escape' && q) onSearchChange('')
          }}
          placeholder="Search by name, email or phone"
          autoComplete="off"
          spellCheck={false}
          maxLength={100}
          className="h-10 w-full rounded-md border border-hairline bg-surface-1 pr-20 pl-3 text-body-sm text-ink placeholder:text-ink-subtle focus-visible:border-primary [&::-webkit-search-cancel-button]:hidden"
        />
        <div className="absolute inset-y-0 right-0 flex items-center">
          {q ? (
            <button
              type="button"
              onClick={() => {
                onSearchChange('')
                searchRef.current?.focus()
              }}
              className="flex h-10 min-w-10 items-center justify-center rounded-md px-3 text-caption font-medium text-ink-subtle hover:bg-surface-2 hover:text-ink"
            >
              Clear
            </button>
          ) : (
            <kbd
              aria-hidden="true"
              className="mr-2.5 rounded-xs border border-hairline bg-canvas px-1.5 font-mono text-caption text-ink-subtle"
            >
              /
            </kbd>
          )}
        </div>
      </div>

      <fieldset className="flex min-w-0 flex-wrap gap-0.5 rounded-md border border-hairline bg-surface-1 p-0.5">
        <legend className="sr-only">Filter by status</legend>
        {FILTERS.map(({ value, label }) => (
          <label key={label} className="relative">
            <input
              type="radio"
              name="status-filter"
              value={value ?? ''}
              checked={status === value}
              onChange={() => onStatusChange(value)}
              className="peer sr-only"
            />
            <span className="flex h-10 cursor-pointer items-center rounded-sm px-3 text-body-sm font-medium text-ink-subtle transition-colors duration-150 select-none peer-checked:bg-canvas peer-checked:text-ink peer-checked:shadow-[0_0_0_1px_var(--hairline)] peer-focus-visible:outline-2 peer-focus-visible:outline-primary hover:text-ink">
              {label}
            </span>
          </label>
        ))}
      </fieldset>
    </div>
  )
}
