import { message, notification } from 'antd'
import type { ArgsProps as MessageArgsProps } from 'antd/es/message'
import type { ArgsProps as NotificationArgsProps } from 'antd/es/notification'

export type ToastType = 'success' | 'error' | 'info' | 'warning' | 'loading'

export interface ToastOptions {
  duration?: number
  onClose?: () => void
  icon?: React.ReactNode
  key?: string
}

/**
 * Toast Notification Service
 * Centralized toast/notification management with consistent styling
 */
export const toast = {
  /**
   * Show success toast
   */
  success: (content: string, options?: ToastOptions) => {
    return message.success({
      content,
      duration: options?.duration ?? 3,
      onClose: options?.onClose,
      icon: options?.icon,
      key: options?.key
    } as MessageArgsProps)
  },

  /**
   * Show error toast
   */
  error: (content: string, options?: ToastOptions) => {
    return message.error({
      content,
      duration: options?.duration ?? 4,
      onClose: options?.onClose,
      icon: options?.icon,
      key: options?.key
    } as MessageArgsProps)
  },

  /**
   * Show info toast
   */
  info: (content: string, options?: ToastOptions) => {
    return message.info({
      content,
      duration: options?.duration ?? 3,
      onClose: options?.onClose,
      icon: options?.icon,
      key: options?.key
    } as MessageArgsProps)
  },

  /**
   * Show warning toast
   */
  warning: (content: string, options?: ToastOptions) => {
    return message.warning({
      content,
      duration: options?.duration ?? 3,
      onClose: options?.onClose,
      icon: options?.icon,
      key: options?.key
    } as MessageArgsProps)
  },

  /**
   * Show loading toast
   */
  loading: (content: string, options?: ToastOptions) => {
    return message.loading({
      content,
      duration: options?.duration ?? 0,
      onClose: options?.onClose,
      icon: options?.icon,
      key: options?.key
    } as MessageArgsProps)
  },

  /**
   * Destroy all toasts
   */
  destroy: () => {
    message.destroy()
  },

  /**
   * Update existing toast
   */
  update: (key: string, options: ToastOptions & { content: string; type?: ToastType }) => {
    const { type = 'info', content, ...rest } = options
    const method = type === 'loading' ? message.loading : 
                   type === 'success' ? message.success :
                   type === 'error' ? message.error :
                   type === 'warning' ? message.warning :
                   message.info
    
    return method({
      content,
      key,
      ...rest
    } as MessageArgsProps)
  }
}

/**
 * Notification Service for more detailed notifications
 */
export const notify = {
  /**
   * Show success notification
   */
  success: (title: string, description?: string, options?: NotificationArgsProps) => {
    return notification.success({
      message: title,
      description,
      placement: 'topRight',
      duration: 4,
      ...options
    })
  },

  /**
   * Show error notification
   */
  error: (title: string, description?: string, options?: NotificationArgsProps) => {
    return notification.error({
      message: title,
      description,
      placement: 'topRight',
      duration: 5,
      ...options
    })
  },

  /**
   * Show info notification
   */
  info: (title: string, description?: string, options?: NotificationArgsProps) => {
    return notification.info({
      message: title,
      description,
      placement: 'topRight',
      duration: 4,
      ...options
    })
  },

  /**
   * Show warning notification
   */
  warning: (title: string, description?: string, options?: NotificationArgsProps) => {
    return notification.warning({
      message: title,
      description,
      placement: 'topRight',
      duration: 4,
      ...options
    })
  },

  /**
   * Show notification with custom content
   */
  open: (options: NotificationArgsProps) => {
    return notification.open({
      placement: 'topRight',
      duration: 4,
      ...options
    })
  },

  /**
   * Close notification by key
   */
  close: (key: string) => {
    notification.close(key)
  },

  /**
   * Destroy all notifications
   */
  destroy: () => {
    notification.destroy()
  }
}

/**
 * Error handler helper
 */
export function showError(error: unknown, fallbackMessage = '操作失败') {
  let message = fallbackMessage
  
  if (error instanceof Error) {
    message = error.message
  } else if (typeof error === 'string') {
    message = error
  } else if (error && typeof error === 'object' && 'message' in error) {
    message = String((error as any).message)
  }

  toast.error(message)
  
  // Log error in development
  if (process.env.NODE_ENV === 'development') {
    console.error('Error:', error)
  }
}

/**
 * Network error handler with retry option
 */
export function showNetworkError(onRetry?: () => void) {
  const key = `network-error-${Date.now()}`
  
  notify.error(
    '网络错误',
    '无法连接到服务器，请检查网络连接',
    {
      key,
      duration: 0,
      btn: onRetry ? (
        <button
          onClick={() => {
            notification.close(key)
            onRetry()
          }}
          style={{
            background: '#1890ff',
            color: 'white',
            border: 'none',
            padding: '4px 12px',
            borderRadius: 4,
            cursor: 'pointer'
          }}
        >
          重试
        </button>
      ) : undefined
    }
  )
}

export default toast
