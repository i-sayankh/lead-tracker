import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { useState } from 'react'
import type { Lead } from '../api/client'
import { LeadForm } from '../components/LeadForm'
import { json, lead, mockFetch } from '../test/fetch'

function Harness({ onCreated }: { onCreated: (lead: Lead) => void }) {
  const [open, setOpen] = useState(true)
  return (
    <LeadForm
      open={open}
      onClose={() => setOpen(false)}
      onCreated={(created) => {
        setOpen(false)
        onCreated(created)
      }}
    />
  )
}

async function fillAndSubmit(values: { name: string; email: string; phone: string }) {
  const user = userEvent.setup()
  await user.type(screen.getByLabelText('Name'), values.name)
  await user.type(screen.getByLabelText('Email'), values.email)
  await user.type(screen.getByLabelText('Phone'), values.phone)
  await user.click(screen.getByRole('button', { name: 'Create lead' }))
}

const conflict = {
  error: {
    code: 'LEAD_EMAIL_CONFLICT',
    message: "A lead with email 'priya@finlytics.in' already exists.",
    details: [{ field: 'body.email', message: 'Email already exists', type: 'conflict' }],
  },
}

describe('LeadForm', () => {
  it('blocks submission and explains an invalid email', async () => {
    const fetch = mockFetch(() => json(201, lead()))
    render(<Harness onCreated={vi.fn()} />)

    await fillAndSubmit({
      name: 'Priya Sharma',
      email: 'priya-at-finlytics',
      phone: '+91 98200 11223',
    })

    const email = screen.getByLabelText('Email')
    expect(email).toHaveAccessibleDescription('Enter a valid email address')
    expect(email).toHaveAttribute('aria-invalid', 'true')
    expect(fetch).not.toHaveBeenCalled()
  })

  it('shows a server 409 under the email field', async () => {
    mockFetch(() => json(409, conflict))
    render(<Harness onCreated={vi.fn()} />)

    await fillAndSubmit({
      name: 'Priya Sharma',
      email: 'Priya@Finlytics.in',
      phone: '+91 98200 11223',
    })

    expect(await screen.findByText('A lead with this email already exists')).toBeInTheDocument()
    expect(screen.getByLabelText('Email')).toHaveAccessibleDescription(
      'A lead with this email already exists',
    )
    expect(screen.getByRole('dialog')).toBeInTheDocument()
  })

  it('maps server validation details onto the matching field', async () => {
    mockFetch(() =>
      json(422, {
        error: {
          code: 'VALIDATION_ERROR',
          message: 'Request validation failed.',
          details: [{ field: 'body.name', message: 'Name is reserved', type: 'value_error' }],
        },
      }),
    )
    render(<Harness onCreated={vi.fn()} />)

    await fillAndSubmit({
      name: 'Priya Sharma',
      email: 'priya@finlytics.in',
      phone: '+91 98200 11223',
    })

    expect(await screen.findByText('Name is reserved')).toBeInTheDocument()
  })

  it('sends trimmed values and closes the dialog on success', async () => {
    const created = lead()
    const fetch = mockFetch(() => json(201, created))
    const onCreated = vi.fn()
    render(<Harness onCreated={onCreated} />)

    await fillAndSubmit({
      name: '  Priya Sharma ',
      email: 'priya@finlytics.in',
      phone: '+91 98200 11223',
    })

    await vi.waitFor(() => expect(onCreated).toHaveBeenCalledWith(created))
    expect(JSON.parse(String(fetch.mock.calls[0]![1]!.body))).toEqual({
      name: 'Priya Sharma',
      email: 'priya@finlytics.in',
      phone: '+91 98200 11223',
      status: 'new',
    })
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })
})
