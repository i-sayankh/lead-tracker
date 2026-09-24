import type { ReactNode } from 'react'

interface Props {
  title: string
  description?: string
  action?: ReactNode
  tone?: 'neutral' | 'error'
}

export function EmptyState({ title, description, action, tone = 'neutral' }: Props) {
  return (
    <div
      role={tone === 'error' ? 'alert' : undefined}
      className="flex flex-col items-center gap-2 rounded-lg border border-dashed border-hairline-strong px-6 py-16 text-center"
    >
      <p className={`text-body-sm font-medium ${tone === 'error' ? 'text-danger' : 'text-ink'}`}>
        {title}
      </p>
      {description && <p className="max-w-sm text-body-sm text-ink-subtle">{description}</p>}
      {action && <div className="mt-3">{action}</div>}
    </div>
  )
}
