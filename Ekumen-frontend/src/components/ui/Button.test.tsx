import React from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { Button } from './Button'

describe('Button Component', () => {
  it('renders with default props', () => {
    render(<Button>Test Button</Button>)
    
    const button = screen.getByRole('button', { name: /test button/i })
    expect(button).toBeInTheDocument()
    expect(button).toHaveClass('btn-agricultural')
    expect(button).toHaveClass('btn-agricultural-primary')
  })

  it('renders with different variants', () => {
    const { rerender } = render(<Button variant="primary">Primary</Button>)
    expect(screen.getByRole('button')).toHaveClass('btn-agricultural-primary')
    
    rerender(<Button variant="secondary">Secondary</Button>)
    expect(screen.getByRole('button')).toHaveClass('btn-secondary')
    
    rerender(<Button variant="success">Success</Button>)
    expect(screen.getByRole('button')).toHaveClass('btn-agricultural-success')
    
    rerender(<Button variant="warning">Warning</Button>)
    expect(screen.getByRole('button')).toHaveClass('btn-agricultural-warning')
    
    rerender(<Button variant="error">Error</Button>)
    expect(screen.getByRole('button')).toHaveClass('btn-agricultural-error')
    
    rerender(<Button variant="outline">Outline</Button>)
    expect(screen.getByRole('button')).toHaveClass('btn-agricultural-outline')
    
    rerender(<Button variant="ghost">Ghost</Button>)
    expect(screen.getByRole('button')).toHaveClass('btn-agricultural-ghost')
  })

  it('renders with different sizes', () => {
    const { rerender } = render(<Button size="sm">Small</Button>)
    expect(screen.getByRole('button')).toHaveClass('btn-sm')
    
    rerender(<Button size="md">Medium</Button>)
    expect(screen.getByRole('button')).not.toHaveClass('btn-sm')
    expect(screen.getByRole('button')).not.toHaveClass('btn-lg')
    
    rerender(<Button size="lg">Large</Button>)
    expect(screen.getByRole('button')).toHaveClass('btn-lg')
  })

  it('handles click events', () => {
    const handleClick = vi.fn()
    render(<Button onClick={handleClick}>Click me</Button>)
    
    const button = screen.getByRole('button')
    fireEvent.click(button)
    
    expect(handleClick).toHaveBeenCalledTimes(1)
  })

  it('is disabled when disabled prop is true', () => {
    render(<Button disabled>Disabled</Button>)
    
    const button = screen.getByRole('button')
    expect(button).toBeDisabled()
    expect(button).toHaveClass('opacity-50', 'cursor-not-allowed')
  })

  it('is disabled when loading prop is true', () => {
    render(<Button loading>Loading</Button>)
    
    const button = screen.getByRole('button')
    expect(button).toBeDisabled()
    expect(button).toHaveClass('opacity-50', 'cursor-not-allowed')
  })

  it('shows loading spinner when loading', () => {
    render(<Button loading>Loading</Button>)
    
    // Check if spinner is present
    const spinner = screen.getByRole('button').querySelector('svg')
    expect(spinner).toBeInTheDocument()
    expect(spinner).toHaveClass('animate-spin')
  })

  it('renders with left and right icons', () => {
    const LeftIcon = () => <span data-testid="left-icon">←</span>
    const RightIcon = () => <span data-testid="right-icon">→</span>
    
    render(
      <Button leftIcon={<LeftIcon />} rightIcon={<RightIcon />}>
        With Icons
      </Button>
    )
    
    expect(screen.getByTestId('left-icon')).toBeInTheDocument()
    expect(screen.getByTestId('right-icon')).toBeInTheDocument()
  })

  it('applies fullWidth class when fullWidth is true', () => {
    render(<Button fullWidth>Full Width</Button>)
    
    expect(screen.getByRole('button')).toHaveClass('w-full')
  })

  it('applies custom className', () => {
    const customClass = 'custom-button-class'
    render(<Button className={customClass}>Custom</Button>)
    
    expect(screen.getByRole('button')).toHaveClass(customClass)
  })

  it('forwards ref correctly', () => {
    const ref = vi.fn()
    render(<Button ref={ref}>Ref Test</Button>)
    
    expect(ref).toHaveBeenCalled()
  })

  it('forwards other props', () => {
    render(<Button data-testid="custom-button" type="submit">Submit</Button>)
    
    const button = screen.getByTestId('custom-button')
    expect(button).toHaveAttribute('type', 'submit')
  })
})
