// 调试面板类型定义

export type LogLevel = 'debug' | 'info' | 'warn' | 'error'

export interface LogEntry {
  id: string
  timestamp: number
  level: LogLevel
  message: string
  source?: string
  line?: number
  details?: any
}

export interface DebugVariable {
  name: string
  value: any
  type: string
  scope: 'local' | 'global' | 'closure'
  expandable?: boolean
  children?: DebugVariable[]
}

export interface StackFrame {
  id: string
  name: string
  file: string
  line: number
  column?: number
  isNative?: boolean
}

export interface DebugError {
  name: string
  message: string
  stack?: StackFrame[]
  timestamp: number
}

export interface DebugState {
  status: 'idle' | 'running' | 'paused' | 'error'
  currentLine?: number
  currentFile?: string
  executionId?: string
}

export interface Breakpoint {
  id: string
  file: string
  line: number
  enabled: boolean
  condition?: string
}

// WebSocket 消息类型
export type DebugMessageType =
  | 'log'
  | 'variables'
  | 'state_change'
  | 'error'
  | 'breakpoint_hit'
  | 'execution_complete'

export interface DebugMessage {
  type: DebugMessageType
  payload: any
  timestamp: number
}

// 调试控制命令
export type DebugCommand =
  | 'continue'
  | 'pause'
  | 'step_over'
  | 'step_into'
  | 'step_out'
  | 'restart'
  | 'stop'

export interface DebugCommandMessage {
  command: DebugCommand
  params?: any
}
