import { useEffect, useId, useRef, useState, type FormEvent } from 'react'
import { ApiError, createLead, LEAD_STATUSES, type Lead, type LeadCreate } from '../api/client'
import { STATUS_LABEL } from '../lib/status'
import { fieldFromApi, validateLead, type FieldErrors, type LeadField } from '../lib/validation'
import { primaryButton, secondaryButton } from './buttons'

interface Props {
  open: boolean
  onClose: () => void
  onCreated: (lead: Lead) => void
}

const EMPTY: LeadCreate = { name: '', email: '', phone: '', status: 'new' }
const TEXT_FIELDS: {
  name: Exclude<LeadField, 'status'>
  label: string
  type: string
  autoComplete: string
  placeholder: string
}[] = [
  { name: 'name', label: 'Name', type: 'text', autoComplete: 'name', placeholder: 'Full name' },
  {
    name: 'email',
    label: 'Email',
    type: 'email',
    autoComplete: 'email',
    placeholder: 'name@company.com',
  },
  {
    name: 'phone',
    label: 'Phone',
    type: 'tel',
    autoComplete: 'tel',
    placeholder: '+91 98200 11223',
  },
]

const input =
  'h-10 w-full rounded-md border bg-surface-1 px-3 text-body-sm text-ink placeholder:text-ink-subtle focus-visible:border-primary aria-[invalid=true]:border-danger'

export function LeadForm({ open, onClose, onCreated }: Props) {
  const dialogRef = useRef<HTMLDialogElement>(null)
  const formRef = useRef<HTMLFormElement>(null)
  const [values, setValues] = useState<LeadCreate>(EMPTY)
  const [touched, setTouched] = useState<Partial<Record<LeadField, boolean>>>({})
  const [serverErrors, setServerErrors] = useState<FieldErrors>({})
  const [formError, setFormError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const id = useId()

  useEffect(() => {
    const dialog = dialogRef.current
    if (!dialog) return
    if (open && !dialog.open) dialog.showModal()
    if (!open && dialog.open) dialog.close()
  }, [open])

  function reset() {
    setValues(EMPTY)
    setTouched({})
    setServerErrors({})
    setFormError(null)
  }

  const clientErrors = validateLead(values)
  const errorFor = (field: LeadField) =>
    serverErrors[field] ?? (touched[field] ? clientErrors[field] : undefined)

  function update(field: Exclude<LeadField, 'status'>, value: string) {
    setValues((v) => ({ ...v, [field]: value }))
    setServerErrors((e) => ({ ...e, [field]: undefined }))
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setTouched({ name: true, email: true, phone: true })
    setFormError(null)
    const firstInvalid = TEXT_FIELDS.find((f) => clientErrors[f.name])
    if (firstInvalid) {
      formRef.current?.querySelector<HTMLInputElement>(`[name="${firstInvalid.name}"]`)?.focus()
      return
    }

    setSubmitting(true)
    try {
      const lead = await createLead({
        name: values.name.trim(),
        email: values.email.trim(),
        phone: values.phone.trim(),
        status: values.status,
      })
      reset()
      onCreated(lead)
    } catch (err) {
      if (!(err instanceof ApiError)) {
        setFormError('Something went wrong. Please try again.')
      } else if (err.code === 'LEAD_EMAIL_CONFLICT') {
        setServerErrors({ email: 'A lead with this email already exists' })
      } else if (err.code === 'VALIDATION_ERROR' && err.details.length > 0) {
        const mapped: FieldErrors = {}
        for (const d of err.details) {
          const field = fieldFromApi(d.field)
          if (field) mapped[field] ??= d.message
        }
        setServerErrors(mapped)
        if (Object.keys(mapped).length === 0) setFormError(err.message)
      } else {
        setFormError(err.message)
      }
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <dialog
      ref={dialogRef}
      aria-labelledby={`${id}-title`}
      onClose={() => {
        reset()
        onClose()
      }}
      className="m-auto w-[calc(100%-2rem)] max-w-md rounded-lg border border-hairline bg-canvas p-0 text-ink"
    >
      <form ref={formRef} noValidate onSubmit={handleSubmit} className="flex flex-col gap-5 p-6">
        <h2 id={`${id}-title`} className="text-card-title font-medium">
          New lead
        </h2>

        {TEXT_FIELDS.map((field) => {
          const error = errorFor(field.name)
          return (
            <div key={field.name} className="flex flex-col gap-1.5">
              <label htmlFor={`${id}-${field.name}`} className="text-body-sm font-medium text-ink">
                {field.label}
              </label>
              <input
                id={`${id}-${field.name}`}
                name={field.name}
                type={field.type}
                autoComplete={field.autoComplete}
                placeholder={field.placeholder}
                value={values[field.name]}
                onChange={(e) => update(field.name, e.target.value)}
                onBlur={() => setTouched((t) => ({ ...t, [field.name]: true }))}
                aria-invalid={error ? true : undefined}
                aria-describedby={error ? `${id}-${field.name}-error` : undefined}
                className={`${input} ${error ? 'border-danger' : 'border-hairline'}`}
              />
              {error && (
                <p id={`${id}-${field.name}-error`} className="text-caption text-danger">
                  {error}
                </p>
              )}
            </div>
          )
        })}

        <div className="flex flex-col gap-1.5">
          <label htmlFor={`${id}-status`} className="text-body-sm font-medium text-ink">
            Status
          </label>
          <select
            id={`${id}-status`}
            name="status"
            value={values.status}
            onChange={(e) => {
              const status = LEAD_STATUSES.find((s) => s === e.target.value)
              if (status) setValues((v) => ({ ...v, status }))
            }}
            className={`${input} border-hairline`}
          >
            {LEAD_STATUSES.map((s) => (
              <option key={s} value={s}>
                {STATUS_LABEL[s]}
              </option>
            ))}
          </select>
        </div>

        {formError && (
          <p role="alert" className="text-body-sm text-danger">
            {formError}
          </p>
        )}

        <div className="flex justify-end gap-2 pt-1">
          <button
            type="button"
            className={secondaryButton}
            onClick={() => dialogRef.current?.close()}
          >
            Cancel
          </button>
          <button type="submit" className={primaryButton} disabled={submitting}>
            {submitting ? 'Creating…' : 'Create lead'}
          </button>
        </div>
      </form>
    </dialog>
  )
}
