import { act, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import App, { SEARCH_DEBOUNCE_MS } from '../App'
import { json, lead, mockFetch, page } from '../test/fetch'

describe('App', () => {
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
