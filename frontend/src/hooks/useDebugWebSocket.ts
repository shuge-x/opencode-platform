import { useEffect, useRef, useState, useCallback } from 'react'
import type { DebugMessage, DebugCommandMessage, DebugState, LogEntry, DebugVariable, DebugError } from '@/types/debug'

interface UseDebugWebSocketOptions {
  skillId: number
  onLog?: (log: LogEntry) => void
  onVariables?: (variables: DebugVariable[]) => void
  onStateChange?: (state: DebugState) => void
  onError?: (error: DebugError) => void
  onConnect?: () => void
  onDisconnect?: () => void
}

export function useDebugWebSocket(options: UseDebugWebSocketOptions) {
  const {
    skillId,
    onLog,
    onVariables,
    onStateChange,
    onError,
    onConnect,
    onDisconnect
  } = options

  const wsRef = useRef<WebSocket | null>(null)
  const [isConnected, setIsConnected] = useState(false)
  const [connectionError, setConnectionError] = useState<string | null>(null)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>()

  const connect = useCallback(() => {
    // 构建 WebSocket URL
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = window.location.host
    const wsUrl = `${protocol}//${host}/api/skills-dev/debug/${skillId}/ws`

    try {
      const ws = new WebSocket(wsUrl)

      ws.onopen = () => {
        console.log('[Debug] WebSocket connected')
        setIsConnected(true)
        setConnectionError(null)
        onConnect?.()
      }

      ws.onmessage = (event) => {
        try {
          const message: DebugMessage = JSON.parse(event.data)
          handleMessage(message)
        } catch (err) {
          console.error('[Debug] Failed to parse message:', err)
        }
      }

      ws.onerror = (event) => {
        console.error('[Debug] WebSocket error:', event)
        setConnectionError('WebSocket connection error')
      }

      ws.onclose = () => {
        console.log('[Debug] WebSocket disconnected')
        setIsConnected(false)
        onDisconnect?.()

        // 5秒后自动重连
        reconnectTimeoutRef.current = setTimeout(() => {
          console.log('[Debug] Attempting to reconnect...')
          connect()
        }, 5000)
      }

      wsRef.current = ws
    } catch (err) {
      console.error('[Debug] Failed to create WebSocket:', err)
      setConnectionError('Failed to create WebSocket connection')
    }
  }, [skillId, onConnect, onDisconnect])

  const handleMessage = useCallback((message: DebugMessage) => {
    switch (message.type) {
      case 'log':
        onLog?.(message.payload as LogEntry)
        break
      case 'variables':
        onVariables?.(message.payload as DebugVariable[])
        break
      case 'state_change':
        onStateChange?.(message.payload as DebugState)
        break
      case 'error':
        onError?.(message.payload as DebugError)
        break
      default:
        console.log('[Debug] Unknown message type:', message.type)
    }
  }, [onLog, onVariables, onStateChange, onError])

  const sendCommand = useCallback((command: DebugCommandMessage) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'command',
        ...command
      }))
      return true
    }
    console.warn('[Debug] Cannot send command: WebSocket not connected')
    return false
  }, [])

  const startDebug = useCallback((params?: { input?: any; breakpoints?: any[] }) => {
    return sendCommand({
      command: 'continue',
      params
    })
  }, [sendCommand])

  const pauseExecution = useCallback(() => {
    return sendCommand({ command: 'pause' })
  }, [sendCommand])

  const continueExecution = useCallback(() => {
    return sendCommand({ command: 'continue' })
  }, [sendCommand])

  const stepOver = useCallback(() => {
    return sendCommand({ command: 'step_over' })
  }, [sendCommand])

  const stepInto = useCallback(() => {
    return sendCommand({ command: 'step_into' })
  }, [sendCommand])

  const stepOut = useCallback(() => {
    return sendCommand({ command: 'step_out' })
  }, [sendCommand])

  const restart = useCallback(() => {
    return sendCommand({ command: 'restart' })
  }, [sendCommand])

  const stop = useCallback(() => {
    return sendCommand({ command: 'stop' })
  }, [sendCommand])

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
    }
    wsRef.current?.close()
  }, [])

  useEffect(() => {
    connect()
    return () => disconnect()
  }, [connect, disconnect])

  return {
    isConnected,
    connectionError,
    sendCommand,
    startDebug,
    pauseExecution,
    continueExecution,
    stepOver,
    stepInto,
    stepOut,
    restart,
    stop,
    reconnect: connect
  }
}
