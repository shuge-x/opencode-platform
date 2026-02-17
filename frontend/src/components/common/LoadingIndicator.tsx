import { useEffect, useState } from 'react'
import { useLocation } from 'react-router-dom'
import './LoadingIndicator.css'

/**
 * 全局顶部进度条加载指示器
 * 在页面路由切换时自动显示
 */
export function LoadingIndicator() {
  const location = useLocation()
  const [loading, setLoading] = useState(false)
  const [progress, setProgress] = useState(0)

  useEffect(() => {
    // 路由变化时开始加载动画
    setLoading(true)
    setProgress(0)

    // 模拟进度增长
    const timer1 = setTimeout(() => setProgress(30), 50)
    const timer2 = setTimeout(() => setProgress(60), 150)
    const timer3 = setTimeout(() => setProgress(90), 300)
    
    // 完成加载
    const completeTimer = setTimeout(() => {
      setProgress(100)
      setTimeout(() => {
        setLoading(false)
        setProgress(0)
      }, 200)
    }, 400)

    return () => {
      clearTimeout(timer1)
      clearTimeout(timer2)
      clearTimeout(timer3)
      clearTimeout(completeTimer)
    }
  }, [location.pathname])

  if (!loading) return null

  return (
    <div className="global-loading-indicator">
      <div 
        className="global-loading-progress" 
        style={{ width: `${progress}%` }}
      />
    </div>
  )
}

/**
 * 可编程的加载进度条
 * 用于手动控制加载状态（如API请求、文件上传等）
 */
interface ProgressBarProps {
  active?: boolean
  progress?: number // 0-100，undefined 表示自动动画
}

export function ProgressBar({ active = false, progress }: ProgressBarProps) {
  const [autoProgress, setAutoProgress] = useState(0)

  useEffect(() => {
    if (!active) {
      setAutoProgress(0)
      return
    }

    // 如果没有指定进度，则自动递增
    if (progress === undefined) {
      setAutoProgress(0)
      const timers: NodeJS.Timeout[] = []
      
      const steps = [20, 40, 60, 75, 85]
      steps.forEach((target, i) => {
        timers.push(setTimeout(() => setAutoProgress(target), (i + 1) * 200))
      })

      return () => timers.forEach(clearTimeout)
    }
  }, [active, progress])

  if (!active) return null

  const currentProgress = progress ?? autoProgress

  return (
    <div className="inline-progress-bar">
      <div 
        className="inline-progress-fill" 
        style={{ width: `${currentProgress}%` }}
      />
    </div>
  )
}

export default LoadingIndicator
