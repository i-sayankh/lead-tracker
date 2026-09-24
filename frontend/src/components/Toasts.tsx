import type { Toast } from '../hooks/useToasts'

interface Props {
  toasts: Toast[]
  onDismiss: (id: number) => void
}

export function Toasts({ toasts, onDismiss }: Props) {
  return (
    <div
      aria-live="polite"
      className="pointer-events-none fixed right-4 bottom-4 left-4 z-50 flex flex-col items-end gap-2 sm:left-auto"
    >
      {toasts.map((toast) => (
        <div
          key={toast.id}
          className="pointer-events-auto flex w-full items-center gap-3 rounded-md border border-hairline bg-surface-2 py-2 pr-2 pl-3 text-body-sm text-ink sm:w-auto sm:min-w-72"
        >
          <span
            aria-hidden="true"
            className={`size-2 shrink-0 rounded-full ${toast.tone === 'error' ? 'bg-danger' : 'bg-success'}`}
          />
          <span className="flex-1">{toast.message}</span>
          <button
            type="button"
            onClick={() => onDismiss(toast.id)}
            aria-label="Dismiss notification"
            className="flex size-8 items-center justify-center rounded-sm text-ink-subtle hover:bg-surface-1 hover:text-ink"
          >
            <svg
              aria-hidden="true"
              viewBox="0 0 16 16"
              className="size-3.5"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
            >
              <path d="M4 4l8 8M12 4l-8 8" />
            </svg>
          </button>
        </div>
      ))}
    </div>
  )
}
