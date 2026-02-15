import { useState, useEffect, useRef, useCallback } from 'react'

/**
 * Debounce Hook
 * Delays updating value until after the specified delay
 */
export function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value)

  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedValue(value)
    }, delay)

    return () => {
      clearTimeout(timer)
    }
  }, [value, delay])

  return debouncedValue
}

/**
 * Throttle Hook
 * Limits how often a value can update
 */
export function useThrottle<T>(value: T, interval: number): T {
  const [throttledValue, setThrottledValue] = useState<T>(value)
  const lastUpdated = useRef<number>(Date.now())

  useEffect(() => {
    const now = Date.now()
    const timeSinceLastUpdate = now - lastUpdated.current

    if (timeSinceLastUpdate >= interval) {
      lastUpdated.current = now
      setThrottledValue(value)
    } else {
      const timer = setTimeout(() => {
        lastUpdated.current = Date.now()
        setThrottledValue(value)
      }, interval - timeSinceLastUpdate)

      return () => clearTimeout(timer)
    }
  }, [value, interval])

  return throttledValue
}

/**
 * Debounced Callback Hook
 * Returns a debounced version of the callback
 */
export function useDebouncedCallback<T extends (...args: any[]) => any>(
  callback: T,
  delay: number
): (...args: Parameters<T>) => void {
  const timeoutRef = useRef<NodeJS.Timeout | null>(null)
  const callbackRef = useRef(callback)

  // Keep callback ref updated
  useEffect(() => {
    callbackRef.current = callback
  }, [callback])

  const debouncedCallback = useCallback((...args: Parameters<T>) => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current)
    }

    timeoutRef.current = setTimeout(() => {
      callbackRef.current(...args)
    }, delay)
  }, [delay])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current)
      }
    }
  }, [])

  return debouncedCallback
}

/**
 * Throttled Callback Hook
 * Returns a throttled version of the callback
 */
export function useThrottledCallback<T extends (...args: any[]) => any>(
  callback: T,
  interval: number
): (...args: Parameters<T>) => void {
  const lastRan = useRef<number>(Date.now())
  const timeoutRef = useRef<NodeJS.Timeout | null>(null)
  const callbackRef = useRef(callback)

  // Keep callback ref updated
  useEffect(() => {
    callbackRef.current = callback
  }, [callback])

  const throttledCallback = useCallback((...args: Parameters<T>) => {
    const now = Date.now()
    const timeSinceLastRan = now - lastRan.current

    if (timeSinceLastRan >= interval) {
      lastRan.current = now
      callbackRef.current(...args)
    } else {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current)
      }

      timeoutRef.current = setTimeout(() => {
        lastRan.current = Date.now()
        callbackRef.current(...args)
      }, interval - timeSinceLastRan)
    }
  }, [interval])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current)
      }
    }
  }, [])

  return throttledCallback
}

/**
 * useRafCallback - Run callback on next animation frame
 */
export function useRafCallback<T extends (...args: any[]) => any>(
  callback: T
): (...args: Parameters<T>) => void {
  const rafRef = useRef<number | null>(null)
  const callbackRef = useRef(callback)

  useEffect(() => {
    callbackRef.current = callback
  }, [callback])

  const rafCallback = useCallback((...args: Parameters<T>) => {
    if (rafRef.current) {
      cancelAnimationFrame(rafRef.current)
    }

    rafRef.current = requestAnimationFrame(() => {
      callbackRef.current(...args)
    })
  }, [])

  useEffect(() => {
    return () => {
      if (rafRef.current) {
        cancelAnimationFrame(rafRef.current)
      }
    }
  }, [])

  return rafCallback
}

/**
 * useIdleCallback - Run callback when browser is idle
 */
export function useIdleCallback<T extends (...args: any[]) => any>(
  callback: T,
  options?: IdleRequestOptions
): (...args: Parameters<T>) => void {
  const idleRef = useRef<number | null>(null)
  const callbackRef = useRef(callback)

  useEffect(() => {
    callbackRef.current = callback
  }, [callback])

  const idleCallback = useCallback((...args: Parameters<T>) => {
    if (idleRef.current) {
      cancelIdleCallback(idleRef.current)
    }

    idleRef.current = requestIdleCallback(() => {
      callbackRef.current(...args)
    }, options)
  }, [options])

  useEffect(() => {
    return () => {
      if (idleRef.current) {
        cancelIdleCallback(idleRef.current)
      }
    }
  }, [])

  return idleCallback
}
