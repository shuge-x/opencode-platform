import React from 'react'
import { render, screen } from '@testing-library/react'
import { 
  LoadingSpinner, 
  LoadingCard, 
  LoadingList, 
  LoadingOverlay,
  PageLoading,
  DelayedLoading 
} from '../Loading'

describe('Loading Components', () => {
  describe('LoadingSpinner', () => {
    it('should render spinner with default props', () => {
      const { container } = render(<LoadingSpinner />)
      expect(container.querySelector('.ant-spin')).toBeInTheDocument()
    })

    it('should render with custom tip', () => {
      render(<LoadingSpinner tip="Loading data..." />)
      expect(screen.getByText('Loading data...')).toBeInTheDocument()
    })

    it('should render small size spinner', () => {
      const { container } = render(<LoadingSpinner size="small" />)
      expect(container.querySelector('.ant-spin')).toBeInTheDocument()
    })

    it('should render large size spinner', () => {
      const { container } = render(<LoadingSpinner size="large" />)
      expect(container.querySelector('.ant-spin')).toBeInTheDocument()
    })

    it('should render fullscreen spinner when fullScreen is true', () => {
      const { container } = render(<LoadingSpinner fullScreen tip="Please wait" />)
      const fullscreenContainer = container.querySelector('[style*="position: fixed"]')
      expect(fullscreenContainer).toBeInTheDocument()
      expect(screen.getByText('Please wait')).toBeInTheDocument()
    })
  })

  describe('LoadingCard', () => {
    it('should render skeleton card', () => {
      const { container } = render(<LoadingCard />)
      expect(container.querySelector('.ant-card')).toBeInTheDocument()
      expect(container.querySelector('.ant-skeleton')).toBeInTheDocument()
    })

    it('should render with custom rows', () => {
      const { container } = render(<LoadingCard rows={5} />)
      expect(container.querySelector('.ant-skeleton')).toBeInTheDocument()
    })

    it('should render without avatar when avatar is false', () => {
      const { container } = render(<LoadingCard avatar={false} />)
      expect(container.querySelector('.ant-skeleton-avatar')).not.toBeInTheDocument()
    })

    it('should render without title when title is false', () => {
      const { container } = render(<LoadingCard title={false} />)
      expect(container.querySelector('.ant-skeleton-title')).not.toBeInTheDocument()
    })
  })

  describe('LoadingList', () => {
    it('should render list with default count', () => {
      const { container } = render(<LoadingList />)
      const cards = container.querySelectorAll('.ant-card')
      expect(cards.length).toBe(5)
    })

    it('should render list with custom count', () => {
      const { container } = render(<LoadingList count={3} />)
      const cards = container.querySelectorAll('.ant-card')
      expect(cards.length).toBe(3)
    })
  })

  describe('LoadingOverlay', () => {
    it('should not render when visible is false', () => {
      const { container } = render(<LoadingOverlay visible={false} />)
      expect(container.firstChild).toBeNull()
    })

    it('should render when visible is true', () => {
      const { container } = render(<LoadingOverlay visible={true} tip="Processing" />)
      expect(container.querySelector('[style*="position: absolute"]')).toBeInTheDocument()
      expect(screen.getByText('Processing')).toBeInTheDocument()
    })

    it('should render without tip', () => {
      const { container } = render(<LoadingOverlay visible={true} />)
      expect(container.querySelector('.ant-spin-large')).toBeInTheDocument()
    })
  })

  describe('PageLoading', () => {
    it('should render full page loading', () => {
      const { container } = render(<PageLoading />)
      expect(container.querySelector('[style*="min-height: 100vh"]')).toBeInTheDocument()
    })

    it('should render with custom tip', () => {
      render(<PageLoading tip="Loading page..." />)
      expect(screen.getByText('Loading page...')).toBeInTheDocument()
    })
  })

  describe('DelayedLoading', () => {
    it('should render children when not loading', () => {
      render(
        <DelayedLoading loading={false}>
          <div>Content</div>
        </DelayedLoading>
      )
      expect(screen.getByText('Content')).toBeInTheDocument()
    })

    it('should render children initially when loading starts', () => {
      render(
        <DelayedLoading loading={true} delay={1000}>
          <div>Content</div>
        </DelayedLoading>
      )
      // Before delay, children should still be visible
      expect(screen.getByText('Content')).toBeInTheDocument()
    })
  })
})
