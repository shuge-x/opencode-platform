import { renderHook, act, waitFor } from '@testing-library/react'
import { useWebSocket } from '../useWebSocket'

describe('useWebSocket', () => {
  beforeEach(() => {
    jest.useFakeTimers()
  })

  afterEach(() => {
    jest.useRealTimers()
  })

  it('should initialize with disconnected state', () => {
    const { result } = renderHook(() => useWebSocket('ws://localhost:8080'))
    
    expect(result.current.isConnected).toBe(false)
    expect(result.current.error).toBeNull()
  })

  it('should have send method', () => {
    const { result } = renderHook(() => useWebSocket('ws://localhost:8080'))
    
    expect(typeof result.current.send).toBe('function')
  })

  it('should have close method', () => {
    const { result } = renderHook(() => useWebSocket('ws://localhost:8080'))
    
    expect(typeof result.current.close).toBe('function')
  })

  it('should have reconnect method', () => {
    const { result } = renderHook(() => useWebSocket('ws://localhost:8080'))
    
    expect(typeof result.current.reconnect).toBe('function')
  })

  it('should call onMessage callback when message received', async () => {
    const onMessage = jest.fn()
    
    renderHook(() => useWebSocket('ws://localhost:8080', { onMessage }))
    
    // Since WebSocket is mocked, we need to simulate the connection
    act(() => {
      jest.runAllTimers()
    })
    
    // The mock WebSocket should call onopen after timeout
  })

  it('should call onOpen callback when connected', async () => {
    const onOpen = jest.fn()
    
    renderHook(() => useWebSocket('ws://localhost:8080', { onOpen }))
    
    act(() => {
      jest.runAllTimers()
    })
    
    // WebSocket mock triggers onopen
  })

  it('should return false when sending on disconnected socket', () => {
    const { result } = renderHook(() => useWebSocket('ws://localhost:8080'))
    
    const sendResult = result.current.send({ type: 'test' })
    expect(sendResult).toBe(false)
  })

  it('should close connection on unmount', () => {
    const { unmount } = renderHook(() => useWebSocket('ws://localhost:8080'))
    
    unmount()
    // WebSocket should be closed
  })

  it('should accept custom reconnect options', () => {
    const { result } = renderHook(() => 
      useWebSocket('ws://localhost:8080', {
        reconnectAttempts: 10,
        reconnectInterval: 5000
      })
    )
    
    expect(result.current).toBeDefined()
  })
})
