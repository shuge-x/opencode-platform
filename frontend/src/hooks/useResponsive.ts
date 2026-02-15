import { useState, useEffect, useCallback } from 'react'

export type Breakpoint = 'xs' | 'sm' | 'md' | 'lg' | 'xl' | 'xxl'

export interface BreakpointConfig {
  xs: number
  sm: number
  md: number
  lg: number
  xl: number
  xxl: number
}

// Ant Design default breakpoints
const DEFAULT_BREAKPOINTS: BreakpointConfig = {
  xs: 0,
  sm: 576,
  md: 768,
  lg: 992,
  xl: 1200,
  xxl: 1600
}

/**
 * Get current breakpoint based on window width
 */
function getBreakpoint(width: number, breakpoints: BreakpointConfig = DEFAULT_BREAKPOINTS): Breakpoint {
  if (width >= breakpoints.xxl) return 'xxl'
  if (width >= breakpoints.xl) return 'xl'
  if (width >= breakpoints.lg) return 'lg'
  if (width >= breakpoints.md) return 'md'
  if (width >= breakpoints.sm) return 'sm'
  return 'xs'
}

/**
 * useBreakpoint Hook
 * Returns current breakpoint and various helper booleans
 */
export function useBreakpoint(breakpoints: BreakpointConfig = DEFAULT_BREAKPOINTS) {
  const [current, setCurrent] = useState<Breakpoint>(() => 
    typeof window !== 'undefined' ? getBreakpoint(window.innerWidth, breakpoints) : 'lg'
  )
  const [dimensions, setDimensions] = useState<{ width: number; height: number }>(() =>
    typeof window !== 'undefined' 
      ? { width: window.innerWidth, height: window.innerHeight }
      : { width: 992, height: 768 }
  )

  useEffect(() => {
    const handleResize = () => {
      const width = window.innerWidth
      const height = window.innerHeight
      setCurrent(getBreakpoint(width, breakpoints))
      setDimensions({ width, height })
    }

    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [breakpoints])

  const breakpointOrder: Breakpoint[] = ['xs', 'sm', 'md', 'lg', 'xl', 'xxl']

  const isAtLeast = useCallback((bp: Breakpoint) => {
    return breakpointOrder.indexOf(current) >= breakpointOrder.indexOf(bp)
  }, [current])

  const isAtMost = useCallback((bp: Breakpoint) => {
    return breakpointOrder.indexOf(current) <= breakpointOrder.indexOf(bp)
  }, [current])

  return {
    current,
    ...dimensions,
    isXs: current === 'xs',
    isSm: current === 'sm',
    isMd: current === 'md',
    isLg: current === 'lg',
    isXl: current === 'xl',
    isXxl: current === 'xxl',
    isMobile: ['xs', 'sm'].includes(current),
    isTablet: current === 'md',
    isDesktop: ['lg', 'xl', 'xxl'].includes(current),
    isAtLeast,
    isAtMost
  }
}

/**
 * useMediaQuery Hook
 * Returns true if the media query matches
 */
export function useMediaQuery(query: string): boolean {
  const [matches, setMatches] = useState<boolean>(() => {
    if (typeof window !== 'undefined') {
      return window.matchMedia(query).matches
    }
    return false
  })

  useEffect(() => {
    const mediaQuery = window.matchMedia(query)
    const handler = (event: MediaQueryListEvent) => setMatches(event.matches)

    // Set initial value
    setMatches(mediaQuery.matches)

    // Listen for changes
    mediaQuery.addEventListener('change', handler)
    return () => mediaQuery.removeEventListener('change', handler)
  }, [query])

  return matches
}

/**
 * Prefabricated media query hooks
 */
export function useIsMobile() {
  return useMediaQuery('(max-width: 575px)')
}

export function useIsTablet() {
  return useMediaQuery('(min-width: 576px) and (max-width: 991px)')
}

export function useIsDesktop() {
  return useMediaQuery('(min-width: 992px)')
}

export function usePrefersDarkMode() {
  return useMediaQuery('(prefers-color-scheme: dark)')
}

export function usePrefersReducedMotion() {
  return useMediaQuery('(prefers-reduced-motion: reduce)')
}

/**
 * useOrientation Hook
 */
export function useOrientation() {
  const [orientation, setOrientation] = useState<'portrait' | 'landscape'>(() => {
    if (typeof window !== 'undefined') {
      return window.innerHeight > window.innerWidth ? 'portrait' : 'landscape'
    }
    return 'landscape'
  })

  useEffect(() => {
    const handleResize = () => {
      setOrientation(window.innerHeight > window.innerWidth ? 'portrait' : 'landscape')
    }

    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [])

  return {
    orientation,
    isPortrait: orientation === 'portrait',
    isLandscape: orientation === 'landscape'
  }
}

/**
 * useContainerQuery Hook
 * Observes container size changes
 */
export function useContainerQuery<T extends HTMLElement = HTMLDivElement>(
  breakpoints: number[] = [576, 768, 992, 1200]
) {
  const ref = useState<T | null>(null)[0]
  const [size, setSize] = useState({ width: 0, height: 0 })
  const [activeBreakpoint, setActiveBreakpoint] = useState(0)

  useEffect(() => {
    if (!ref) return

    const observer = new ResizeObserver((entries) => {
      for (const entry of entries) {
        const { width, height } = entry.contentRect
        setSize({ width, height })

        // Find the largest breakpoint that fits
        const matching = breakpoints.filter(bp => width >= bp)
        setActiveBreakpoint(matching.length > 0 ? Math.max(...matching) : 0)
      }
    })

    observer.observe(ref)
    return () => observer.disconnect()
  }, [ref, breakpoints])

  return { ref, ...size, activeBreakpoint }
}
