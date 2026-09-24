import type { LeadCreate } from '../api/client'

export type LeadField = 'name' | 'email' | 'phone' | 'status'
export type FieldErrors = Partial<Record<LeadField, string>>

// Mirrors backend/app/schemas.py (LeadCreate). The server stays the source of truth;
// this only gives faster feedback.
const EMAIL = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
const PHONE = /^\+?[0-9]{7,15}$/
const PHONE_SEPARATORS = /[\s\-.()]/g
export const PHONE_RULE = 'Phone must contain 7–15 digits, optionally prefixed with +'

export function validateLead(values: LeadCreate): FieldErrors {
  const errors: FieldErrors = {}
  const name = values.name.trim()
  const email = values.email.trim()
  const phone = values.phone.trim()

  if (!name) errors.name = 'Name is required'
  else if (name.length > 100) errors.name = 'Name must be 100 characters or fewer'

  if (!email) errors.email = 'Email is required'
  else if (email.length > 254 || !EMAIL.test(email)) errors.email = 'Enter a valid email address'

  if (!phone) errors.phone = 'Phone is required'
  else if (!PHONE.test(phone.replace(PHONE_SEPARATORS, ''))) errors.phone = PHONE_RULE

  return errors
}

/** Maps API error details ("body.email") onto form fields ("email"). */
export function fieldFromApi(field: string): LeadField | null {
  const name = field.split('.')[1]
  return name === 'name' || name === 'email' || name === 'phone' || name === 'status' ? name : null
}
