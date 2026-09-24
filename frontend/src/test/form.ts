import { screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

/** Fills the "New lead" dialog and submits it. */
export async function fillAndSubmitLead(values: { name: string; email: string; phone: string }) {
  const user = userEvent.setup()
  const dialog = within(screen.getByRole('dialog'))
  await user.type(dialog.getByLabelText('Name'), values.name)
  await user.type(dialog.getByLabelText('Email'), values.email)
  await user.type(dialog.getByLabelText('Phone'), values.phone)
  await user.click(dialog.getByRole('button', { name: 'Create lead' }))
}
