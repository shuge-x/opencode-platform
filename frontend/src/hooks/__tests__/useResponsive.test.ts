import { renderHook, act } from '@testing-library/react'
import { useBreakpoint, useMediaQuery, useIsMobile, useIsTablet, useIsDesktop, useOrientation } from '../useResponsive'

describe('useResponsive hooks', () => {
  describe('useBreakpoint', () => {
    it('should return current breakpoint', () => {
      const { result } = renderHook(() => useBreakpoint())
      
      expect(result.current.current).toBeDefined()
      expect(['xs', 'sm', 'md', 'lg', 'xl', 'xxl']).toContain(result.current.current)
    })

    it('should return dimensions', () => {
      const { result } = renderHook(() => useBreakpoint())
      
      expect(result.current.width).toBeGreaterThan(0)
      expect(result.current.height).toBeGreaterThan(0)
    })

    it('should have boolean helpers for breakpoints', () => {
      const { result } = renderHook(() => useBreakpoint())
      
      expect(typeof result.current.isXs).toBe('boolean')
      expect(typeof result.current.isSm).toBe('boolean')
      expect(typeof result.current.isMd).toBe('boolean')
      expect(typeof result.current.isLg).toBe('boolean')
      expect(typeof result.current.isXl).toBe('boolean')
      expect(typeof result.current.isXxl).toBe('boolean')
    })

    it('should have device type helpers', () => {
      const { result } = renderHook(() => useBreakpoint())
      
      expect(typeof result.current.isMobile).toBe('boolean')
      expect(typeof result.current.isTablet).toBe('boolean')
      expect(typeof result.current.isDesktop).toBe('boolean')
    })

    it('should have isAtLeast method', () => {
      const { result } = renderHook(() => useBreakpoint())
      
      expect(typeof result.current.isAtLeast).toBe('function')
      expect(typeof result.current.isAtLeast('md')).toBe('boolean')
    })

    it('should have isAtMost method', () => {
      const { result } = renderHook(() => useBreakpoint())
      
      expect(typeof result.current.isAtMost).toBe('function')
      expect(typeof result.current.isAtMost('md')).toBe('boolean')
    })

    it('should correctly identify only one breakpoint at a time', () => {
      const { result } = renderHook(() => useBreakpoint())
      
      const breakpoints = ['isXs', 'isSm', 'isMd', 'isLg', 'isXl', 'isXxl'] as const
      const activeCount = breakpoints.filter(bp => result.current[bp]).length
      expect(activeCount).toBe(1)
    })
  })

  describe('useMediaQuery', () => {
    it('should return boolean for media query', () => {
      const { result } = renderHook(() => useMediaQuery('(min-width: 768px)'))
      
      expect(typeof result.current).toBe('boolean')
    })

    it('should return false for impossible query', () => {
      const { result } = renderHook(() => useMediaQuery('(min-width: 99999px)'))
      
      expect(result.current).toBe(false)
    })
  })

  describe('useIsMobile', () => {
    it('should return boolean', () => {
      const { result } = renderHook(() => useIsMobile())
      
      expect(typeof result.current).toBe('boolean')
    })
  })

  describe('useIsTablet', () => {
    it('should return boolean', () => {
      const { result } = renderHook(() => useIsTablet())
      
      expect(typeof result.current).toBe('boolean')
    })
  })

  describe('useIsDesktop', () => {
    it('should return boolean', () => {
      const { result } = renderHook(() => useIsDesktop())
      
      expect(typeof result.current).toBe('boolean')
    })
  })

  describe('useOrientation', () => {
    it('should return orientation', () => {
      const { result } = renderHook(() => useOrientation())
      
      expect(['portrait', 'landscape']).toContain(result.current.orientation)
    })

    it('should have isPortrait helper', () => {
      const { result } = renderHook(() => useOrientation())
      
      expect(typeof result.current.isPortrait).toBe('boolean')
    })

    it('should have isLandscape helper', () => {
      const { result } = renderHook(() => useOrientation())
      
      expect(typeof result.current.isLandscape).toBe('boolean')
    })

    it('should have correct boolean values', () => {
      const { result } = renderHook(() => useOrientation())
      
      // isPortrait and isLandscape should be opposites
      expect(result.current.isPortrait).toBe(!result.current.isLandscape)
    })
  })
})
