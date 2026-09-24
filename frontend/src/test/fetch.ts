import { vi } from 'vitest'
import type { Lead, LeadPage } from '../api/client'

export function json(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

export function lead(overrides: Partial<Lead> = {}): Lead {
  return {
    id: '3f1c2a9e-8b7d-4c1e-9f0a-2b6d5e4c3a21',
    name: 'Priya Sharma',
    email: 'priya@finlytics.in',
    phone: '+919820011223',
    status: 'new',
    created_at: '2026-09-24T10:15:30+00:00',
    ...overrides,
  }
}

export function page(items: Lead[], total = items.length): LeadPage {
  return { items, total, limit: 20, offset: 0 }
}

/** Replaces global fetch; `handler` gets the request URL and init and returns a Response. */
export function mockFetch(handler: (url: URL, init: RequestInit) => Response | Promise<Response>) {
  const fn = vi.fn((input: RequestInfo | URL, init: RequestInit = {}) =>
    Promise.resolve(handler(new URL(String(input)), init)),
  )
  vi.stubGlobal('fetch', fn)
  return fn
}
