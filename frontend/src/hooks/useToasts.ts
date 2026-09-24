import { useCallback, useEffect, useRef, useState } from 'react'

export interface Toast {
  id: number
  message: string
  tone: 'success' | 'error'
}

export const TOAST_DURATION_MS = 4000

export function useToasts() {
  const [toasts, setToasts] = useState<Toast[]>([])
  const nextId = useRef(0)
  const timers = useRef(new Map<number, ReturnType<typeof setTimeout>>())

  const dismiss = useCallback((id: number) => {
    clearTimeout(timers.current.get(id))
    timers.current.delete(id)
    setToasts((all) => all.filter((t) => t.id !== id))
  }, [])

  const push = useCallback(
    (message: string, tone: Toast['tone'] = 'success') => {
      const id = nextId.current++
      setToasts((all) => [...all, { id, message, tone }])
      timers.current.set(
        id,
        setTimeout(() => dismiss(id), TOAST_DURATION_MS),
      )
    },
    [dismiss],
  )

  useEffect(() => {
    const pending = timers.current
    return () => pending.forEach(clearTimeout)
  }, [])

  return { toasts, push, dismiss }
}
