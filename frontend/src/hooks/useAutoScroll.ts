import { useEffect, useRef, type RefObject } from 'react'

export function useAutoScroll<T extends HTMLElement>(
  deps: unknown[]
): RefObject<T | null> {
  const ref = useRef<T | null>(null)

  useEffect(() => {
    const el = ref.current
    if (el) {
      el.scrollTo({
        top: el.scrollHeight,
        behavior: 'smooth',
      })
    }
  }, deps)

  return ref
}
