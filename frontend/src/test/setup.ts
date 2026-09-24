import '@testing-library/jest-dom/vitest'
import { afterEach, vi } from 'vitest'

// jsdom does not implement <dialog>; this covers what LeadForm uses.
if (!HTMLDialogElement.prototype.showModal) {
  HTMLDialogElement.prototype.showModal = function (this: HTMLDialogElement) {
    this.open = true
  }
  HTMLDialogElement.prototype.close = function (this: HTMLDialogElement) {
    if (!this.open) return
    this.open = false
    this.dispatchEvent(new Event('close'))
  }
}

afterEach(() => {
  vi.unstubAllGlobals()
  vi.useRealTimers()
  window.history.replaceState(null, '', '/')
})
