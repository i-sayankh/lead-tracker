import type { components, operations } from './schema'

type Schemas = components['schemas']

export type Lead = Schemas['LeadRead']
export type LeadPage = Schemas['LeadPage']
export type LeadCreate = Schemas['LeadCreate']
export type LeadStatus = Schemas['LeadStatus']
export type ErrorResponse = Schemas['ErrorResponse']
export type ErrorDetail = Schemas['ErrorDetail']
/** Server error codes, plus NETWORK_ERROR for requests that never got a response. */
export type ErrorCode = Schemas['ErrorCode'] | 'NETWORK_ERROR'
export type ListLeadsParams = NonNullable<operations['list_leads']['parameters']['query']>

export const LEAD_STATUSES: readonly LeadStatus[] = ['new', 'contacted', 'qualified', 'lost']

const BASE: string = import.meta.env.VITE_API_BASE_URL
if (!BASE) {
  throw new Error('VITE_API_BASE_URL is not set. Copy frontend/.env.example to frontend/.env.')
}

export class ApiError extends Error {
  readonly status: number
  readonly code: ErrorCode
  readonly details: ErrorDetail[]

  constructor(status: number, code: ErrorCode, message: string, details: ErrorDetail[] = []) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.code = code
    this.details = details
  }
}

function isErrorResponse(body: unknown): body is ErrorResponse {
  if (typeof body !== 'object' || body === null || !('error' in body)) return false
  const error = (body as { error: unknown }).error
  return typeof error === 'object' && error !== null && 'code' in error && 'message' in error
}

function isAbort(err: unknown): boolean {
  return err instanceof DOMException && err.name === 'AbortError'
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  let response: Response
  try {
    response = await fetch(`${BASE}${path}`, {
      ...init,
      headers: init.body ? { 'Content-Type': 'application/json' } : undefined,
    })
  } catch (err) {
    if (isAbort(err)) throw err
    throw new ApiError(0, 'NETWORK_ERROR', 'Could not reach the server. Check your connection.')
  }

  let body: unknown
  try {
    body = await response.json()
  } catch (err) {
    if (isAbort(err)) throw err
    body = null
  }
  if (response.ok) {
    // A 2xx without a JSON body means we are not talking to this API (e.g. a wrong base URL
    // serving an HTML page); never hand callers `null` typed as data.
    if (body === null) {
      throw new ApiError(
        response.status,
        'INTERNAL_ERROR',
        'The server sent an unexpected response.',
      )
    }
    return body as T
  }
  if (isErrorResponse(body)) {
    const { code, message, details } = body.error
    throw new ApiError(response.status, code, message, details ?? [])
  }
  throw new ApiError(response.status, 'INTERNAL_ERROR', `Unexpected response (${response.status}).`)
}

export function listLeads(params: ListLeadsParams, signal?: AbortSignal): Promise<LeadPage> {
  const query = new URLSearchParams()
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null && value !== '') query.set(key, String(value))
  }
  const qs = query.toString()
  return request<LeadPage>(`/api/v1/leads${qs ? `?${qs}` : ''}`, { signal })
}

export function createLead(body: LeadCreate, signal?: AbortSignal): Promise<Lead> {
  return request<Lead>('/api/v1/leads', { method: 'POST', body: JSON.stringify(body), signal })
}

export function updateLeadStatus(id: string, status: LeadStatus): Promise<Lead> {
  return request<Lead>(`/api/v1/leads/${encodeURIComponent(id)}/status`, {
    method: 'PATCH',
    body: JSON.stringify({ status }),
  })
}
