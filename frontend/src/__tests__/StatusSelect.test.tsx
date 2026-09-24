import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { useState } from 'react'
import type { Lead } from '../api/client'
import { StatusSelect } from '../components/StatusSelect'
import { Toasts } from '../components/Toasts'
import { useToasts } from '../hooks/useToasts'
import { json, lead, mockFetch } from '../test/fetch'

/** Mirrors how App uses StatusSelect: the parent owns the lead and shows toasts. */
function Harness({ initial }: { initial: Lead }) {
  const [current, setCurrent] = useState(initial)
  const { toasts, push, dismiss } = useToasts()
  return (
    <>
      <StatusSelect lead={current} onUpdated={setCurrent} onError={(m) => push(m, 'error')} />
      <Toasts toasts={toasts} onDismiss={dismiss} />
    </>
  )
}

describe('StatusSelect', () => {
  it('shows the new status immediately and disables the select until the server answers', async () => {
    let respond: (response: Response) => void = () => {}
    mockFetch(() => new Promise<Response>((resolve) => (respond = resolve)))
    const user = userEvent.setup()
    render(<Harness initial={lead({ status: 'new' })} />)
    const select = screen.getByLabelText('Status for Priya Sharma')

    await user.selectOptions(select, 'qualified')

    expect(select).toHaveValue('qualified')
    expect(select).toBeDisabled()

    respond(json(200, lead({ status: 'qualified' })))

    await vi.waitFor(() => expect(select).toBeEnabled())
    expect(select).toHaveValue('qualified')
  })

  it('rolls back and shows an error toast when the update fails', async () => {
    mockFetch(() =>
      json(404, {
        error: { code: 'LEAD_NOT_FOUND', message: "Lead '3f1c' was not found.", details: null },
      }),
    )
    const user = userEvent.setup()
    render(<Harness initial={lead({ status: 'contacted' })} />)
    const select = screen.getByLabelText('Status for Priya Sharma')

    await user.selectOptions(select, 'lost')

    expect(
      await screen.findByText("Couldn't update Priya Sharma to Lost. Lead '3f1c' was not found."),
    ).toBeInTheDocument()
    expect(select).toHaveValue('contacted')
    expect(select).toBeEnabled()
  })
})
