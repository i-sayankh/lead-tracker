import { act, render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import App, { SEARCH_DEBOUNCE_MS } from '../App'
import { emailConflict, errorBody, json, lead, mockFetch, page } from '../test/fetch'
import { fillAndSubmitLead } from '../test/form'

const serverError = errorBody('INTERNAL_ERROR', 'An unexpected error occurred.')

describe('App', () => {
  it('replaces the table with the error state when the request for a new filter fails', async () => {
    mockFetch((url) =>
      url.searchParams.get('status') === 'lost'
        ? json(500, serverError)
        : json(200, page([lead()])),
    )
    const user = userEvent.setup()
    render(<App />)
    await screen.findByRole('cell', { name: 'Priya Sharma' })

    await user.click(screen.getByText('Lost', { selector: 'span' }))

    expect(await screen.findByText("Couldn't load leads")).toBeInTheDocument()
    expect(screen.queryByRole('cell', { name: 'Priya Sharma' })).not.toBeInTheDocument()
  })

  it('does not flash the empty-database state while switching away from an empty filter', async () => {
    window.history.replaceState(null, '', '/?status=lost')
    let respondAll: (r: Response) => void = () => {}
    mockFetch((url) =>
      url.searchParams.has('status')
        ? json(200, page([]))
        : new Promise<Response>((resolve) => (respondAll = resolve)),
    )
    const user = userEvent.setup()
    render(<App />)
    await screen.findByText('No lost leads yet')

    await user.click(screen.getByText('All', { selector: 'span' }))

    expect(screen.queryByText('No leads yet')).not.toBeInTheDocument()
    respondAll(json(200, page([lead()])))
    expect(await screen.findByRole('cell', { name: 'Priya Sharma' })).toBeInTheDocument()
  })

  it('clears filters after creating a lead so the new lead is visible', async () => {
    window.history.replaceState(null, '', '/?status=lost')
    const created = lead({ id: '9b2e0000-0000-4000-8000-000000000001', name: 'Omar Haddad' })
    mockFetch((url, init) => {
      if (init.method === 'POST') return json(201, created)
      return json(200, url.searchParams.has('status') ? page([]) : page([created]))
    })
    const user = userEvent.setup()
    render(<App />)
    await screen.findByText('No lost leads yet')

    await user.click(screen.getByRole('button', { name: 'New lead' }))
    await fillAndSubmitLead({
      name: 'Omar Haddad',
      email: 'omar@haddad.co',
      phone: '+971 50 555 0100',
    })

    expect(await screen.findByRole('cell', { name: 'Omar Haddad' })).toBeInTheDocument()
    expect(window.location.search).toBe('')
  })

  it('does not show a late server error in a create form that was closed and reopened', async () => {
    let respond: (r: Response) => void = () => {}
    mockFetch((_url, init) =>
      init.method === 'POST'
        ? new Promise<Response>((resolve) => (respond = resolve))
        : json(200, page([lead()])),
    )
    const user = userEvent.setup()
    render(<App />)
    await screen.findByRole('cell', { name: 'Priya Sharma' })

    await user.click(screen.getByRole('button', { name: 'New lead' }))
    await fillAndSubmitLead({
      name: 'Priya Sharma',
      email: 'priya@finlytics.in',
      phone: '+91 98200 11223',
    })
    await user.click(screen.getByRole('button', { name: 'Cancel' }))
    await act(async () => respond(json(409, emailConflict)))
    await user.click(screen.getByRole('button', { name: 'New lead' }))

    expect(screen.queryByText('A lead with this email already exists')).not.toBeInTheDocument()
    expect(within(screen.getByRole('dialog')).getByLabelText('Email')).toHaveValue('')
  })

  it('ignores a create that succeeds after its form was cancelled', async () => {
    let respond: (r: Response) => void = () => {}
    mockFetch((_url, init) =>
      init.method === 'POST'
        ? new Promise<Response>((resolve) => (respond = resolve))
        : json(200, page([lead()])),
    )
    const user = userEvent.setup()
    render(<App />)
    await screen.findByRole('cell', { name: 'Priya Sharma' })

    await user.click(screen.getByRole('button', { name: 'New lead' }))
    await fillAndSubmitLead({ name: 'Late Lead', email: 'late@lead.io', phone: '+1 415 555 0100' })
    await user.click(screen.getByRole('button', { name: 'Cancel' }))
    await user.click(screen.getByRole('button', { name: 'New lead' }))
    await act(async () => respond(json(201, lead({ name: 'Late Lead' }))))

    expect(screen.getByRole('dialog')).toBeInTheDocument()
    expect(screen.queryByText('Lead created')).not.toBeInTheDocument()
  })

  it('shows the empty state when there are no leads at all', async () => {
    mockFetch(() => json(200, page([])))
    render(<App />)

    expect(await screen.findByText('No leads yet')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Create your first lead' })).toBeInTheDocument()
  })

  it('shows a no-results state whose button clears the filters', async () => {
    window.history.replaceState(null, '', '/?q=zzz')
    const fetch = mockFetch((url) =>
      json(200, url.searchParams.has('q') ? page([]) : page([lead()])),
    )
    const user = userEvent.setup()
    render(<App />)

    expect(await screen.findByText('No leads match “zzz”')).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Clear filters' }))

    expect(await screen.findByRole('cell', { name: 'Priya Sharma' })).toBeInTheDocument()
    expect(window.location.search).toBe('')
    expect(new URL(String(fetch.mock.lastCall![0])).searchParams.has('q')).toBe(false)
  })

  it('searches only after typing pauses for the debounce delay', async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true })
    const fetch = mockFetch(() => json(200, page([lead()])))
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime })
    render(<App />)
    await screen.findByRole('cell', { name: 'Priya Sharma' })
    const callsBefore = fetch.mock.calls.length

    await user.type(screen.getByLabelText('Search leads'), 'pri')
    expect(window.location.search).toBe('?q=pri')
    expect(fetch).toHaveBeenCalledTimes(callsBefore)

    await act(() => vi.advanceTimersByTimeAsync(SEARCH_DEBOUNCE_MS))

    expect(fetch).toHaveBeenCalledTimes(callsBefore + 1)
    expect(new URL(String(fetch.mock.lastCall![0])).searchParams.get('q')).toBe('pri')
  })
})
