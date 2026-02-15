import { useEffect, useCallback, useRef, useState } from 'react'

export interface KeyboardShortcut {
  key: string
  ctrl?: boolean
  shift?: boolean
  alt?: boolean
  meta?: boolean
  action: () => void
  description?: string
  preventDefault?: boolean
  stopPropagation?: boolean
  enabled?: boolean
}

export interface UseKeyboardShortcutsOptions {
  enabled?: boolean
  scope?: string
}

/**
 * Normalize key string for consistent comparison
 */
function normalizeKey(key: string): string {
  return key.toLowerCase().trim()
}

/**
 * Check if keyboard event matches shortcut
 */
function matchesShortcut(
  event: KeyboardEvent,
  shortcut: KeyboardShortcut
): boolean {
  const keyMatch = normalizeKey(event.key) === normalizeKey(shortcut.key)
  const ctrlMatch = !!shortcut.ctrl === (event.ctrlKey || event.metaKey)
  const shiftMatch = !!shortcut.shift === event.shiftKey
  const altMatch = !!shortcut.alt === event.altKey
  // Note: meta key is treated as ctrl for cross-platform compatibility

  return keyMatch && ctrlMatch && shiftMatch && altMatch
}

/**
 * useKeyboardShortcuts Hook
 * Register and handle keyboard shortcuts
 */
export function useKeyboardShortcuts(
  shortcuts: KeyboardShortcut[],
  options: UseKeyboardShortcutsOptions = {}
) {
  const { enabled = true } = options
  const shortcutsRef = useRef(shortcuts)

  // Keep shortcuts ref updated
  useEffect(() => {
    shortcutsRef.current = shortcuts
  }, [shortcuts])

  useEffect(() => {
    if (!enabled) return

    const handleKeyDown = (event: KeyboardEvent) => {
      // Don't trigger shortcuts when typing in inputs
      const target = event.target as HTMLElement
      const isInput = ['INPUT', 'TEXTAREA', 'SELECT'].includes(target.tagName) ||
        target.isContentEditable

      for (const shortcut of shortcutsRef.current) {
        // Skip disabled shortcuts
        if (shortcut.enabled === false) continue

        // Skip if typing in input unless specifically allowed
        if (isInput && !shortcut.ctrl && !shortcut.meta) continue

        if (matchesShortcut(event, shortcut)) {
          if (shortcut.preventDefault !== false) {
            event.preventDefault()
          }
          if (shortcut.stopPropagation) {
            event.stopPropagation()
          }
          shortcut.action()
          return
        }
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [enabled])

  // Return shortcuts for documentation/debugging
  return {
    shortcuts: shortcuts.map(s => ({
      key: s.key,
      modifiers: [
        s.ctrl && 'Ctrl',
        s.shift && 'Shift',
        s.alt && 'Alt',
        s.meta && 'Meta'
      ].filter(Boolean).join('+'),
      description: s.description
    }))
  }
}

/**
 * Common keyboard shortcuts factory
 */
export function createShortcuts(
  shortcuts: Array<{
    key: string
    ctrl?: boolean
    shift?: boolean
    alt?: boolean
    action: () => void
    description?: string
  }>
): KeyboardShortcut[] {
  return shortcuts.map(s => ({
    ...s,
    preventDefault: true,
    enabled: true
  }))
}

/**
 * useKeyPress Hook
 * Simple hook to detect if a key is currently pressed
 */
export function useKeyPress(targetKey: string): boolean {
  const [keyPressed, setKeyPressed] = useState(false)

  useEffect(() => {
    const downHandler = (event: KeyboardEvent) => {
      if (normalizeKey(event.key) === normalizeKey(targetKey)) {
        setKeyPressed(true)
      }
    }

    const upHandler = (event: KeyboardEvent) => {
      if (normalizeKey(event.key) === normalizeKey(targetKey)) {
        setKeyPressed(false)
      }
    }

    window.addEventListener('keydown', downHandler)
    window.addEventListener('keyup', upHandler)

    return () => {
      window.removeEventListener('keydown', downHandler)
      window.removeEventListener('keyup', upHandler)
    }
  }, [targetKey])

  return keyPressed
}

/**
 * useEscapeKey Hook
 * Specialized hook for escape key handling
 */
export function useEscapeKey(callback: () => void, enabled = true) {
  useEffect(() => {
    if (!enabled) return

    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        event.preventDefault()
        callback()
      }
    }

    window.addEventListener('keydown', handleEscape)
    return () => window.removeEventListener('keydown', handleEscape)
  }, [callback, enabled])
}

/**
 * useEnterKey Hook
 * Specialized hook for enter key handling
 */
export function useEnterKey(callback: () => void, enabled = true) {
  useEffect(() => {
    if (!enabled) return

    const handleEnter = (event: KeyboardEvent) => {
      if (event.key === 'Enter' && !event.shiftKey) {
        const target = event.target as HTMLElement
        const isInput = ['INPUT', 'TEXTAREA'].includes(target.tagName)
        
        if (isInput) {
          event.preventDefault()
          callback()
        }
      }
    }

    window.addEventListener('keydown', handleEnter)
    return () => window.removeEventListener('keydown', handleEnter)
  }, [callback, enabled])
}

/**
 * useArrowNavigation Hook
 * Navigate through items with arrow keys
 */
export function useArrowNavigation(
  itemCount: number,
  options: {
    enabled?: boolean
    loop?: boolean
    onSelect?: (index: number) => void
    initialIndex?: number
  } = {}
) {
  const { enabled = true, loop = true, onSelect, initialIndex = 0 } = options
  const [selectedIndex, setSelectedIndex] = useState(initialIndex)

  const handleKeyDown = useCallback((event: KeyboardEvent) => {
    if (!enabled) return

    // Don't handle if in input
    const target = event.target as HTMLElement
    if (['INPUT', 'TEXTAREA'].includes(target.tagName)) return

    let newIndex = selectedIndex

    switch (event.key) {
      case 'ArrowUp':
        event.preventDefault()
        if (selectedIndex > 0) {
          newIndex = selectedIndex - 1
        } else if (loop) {
          newIndex = itemCount - 1
        }
        break
      case 'ArrowDown':
        event.preventDefault()
        if (selectedIndex < itemCount - 1) {
          newIndex = selectedIndex + 1
        } else if (loop) {
          newIndex = 0
        }
        break
      case 'Enter':
        event.preventDefault()
        onSelect?.(selectedIndex)
        return
      default:
        return
    }

    setSelectedIndex(newIndex)
  }, [enabled, itemCount, loop, selectedIndex, onSelect])

  useEffect(() => {
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [handleKeyDown])

  return { selectedIndex, setSelectedIndex }
}
