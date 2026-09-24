import { ApiError, createLead, listLeads } from '../api/client'
import { json, lead, mockFetch, page } from '../test/fetch'

describe('api client', () => {
  it('parses the error envelope into an ApiError', async () => {
    mockFetch(() =>
      json(409, {
        error: {
          code: 'LEAD_EMAIL_CONFLICT',
          message: "A lead with email 'priya@finlytics.in' already exists.",
          details: [{ field: 'body.email', message: 'Email already exists', type: 'conflict' }],
        },
      }),
    )

    const error = await createLead({
      name: 'Priya',
      email: 'priya@finlytics.in',
      phone: '+919820011223',
    }).catch((e: unknown) => e)

    expect(error).toBeInstanceOf(ApiError)
    expect(error).toMatchObject({
      status: 409,
      code: 'LEAD_EMAIL_CONFLICT',
      message: "A lead with email 'priya@finlytics.in' already exists.",
      details: [{ field: 'body.email', message: 'Email already exists', type: 'conflict' }],
    })
  })

  it('turns a network failure into a NETWORK_ERROR', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('Failed to fetch')))

    await expect(listLeads({})).rejects.toMatchObject({ status: 0, code: 'NETWORK_ERROR' })
  })

  it('falls back to INTERNAL_ERROR when an error response is not the envelope', async () => {
    mockFetch(() => new Response('<html>Bad gateway</html>', { status: 502 }))

    await expect(listLeads({})).rejects.toMatchObject({ status: 502, code: 'INTERNAL_ERROR' })
  })

  it('sends only the list parameters that are set', async () => {
    const fetch = mockFetch(() => json(200, page([lead()])))

    const result = await listLeads({ q: 'priya', status: null, limit: 20, offset: 0 })

    expect(result.items).toHaveLength(1)
    expect(String(fetch.mock.calls[0]![0])).toBe(
      'http://api.test/api/v1/leads?q=priya&limit=20&offset=0',
    )
  })
})
