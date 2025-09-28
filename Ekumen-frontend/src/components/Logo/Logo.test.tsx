import React from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { Logo } from './Logo'

describe('Logo Component', () => {
  it('renders with default props', () => {
    render(<Logo />)
    
    // Check if the logo container is rendered
    const logoContainer = screen.getByText('Assistant Agricole IA').closest('div')
    expect(logoContainer).toBeInTheDocument()
    
    // Check if default text is rendered
    expect(screen.getByText('Assistant Agricole IA')).toBeInTheDocument()
  })

  it('renders with custom text', () => {
    const customText = 'Mon Assistant'
    render(<Logo text={customText} />)
    
    expect(screen.getByText(customText)).toBeInTheDocument()
  })

  it('renders without text when showText is false', () => {
    render(<Logo showText={false} />)
    
    // Text should not be present
    expect(screen.queryByText('Assistant Agricole IA')).not.toBeInTheDocument()
    
    // But container should still be present
    const logoContainer = document.querySelector('.logo')
    expect(logoContainer).toBeInTheDocument()
  })

  it('applies correct size classes', () => {
    const { rerender } = render(<Logo size="sm" />)
    expect(document.querySelector('.logo')).toHaveClass('logo-sm')
    
    rerender(<Logo size="md" />)
    expect(document.querySelector('.logo')).toHaveClass('logo-md')
    
    rerender(<Logo size="lg" />)
    expect(document.querySelector('.logo')).toHaveClass('logo-lg')
    
    rerender(<Logo size="xl" />)
    expect(document.querySelector('.logo')).toHaveClass('logo-xl')
  })

  it('handles click events when clickable', () => {
    const handleClick = vi.fn()
    render(<Logo clickable={true} onClick={handleClick} />)
    
    const logoButton = screen.getByRole('button')
    fireEvent.click(logoButton)
    
    expect(handleClick).toHaveBeenCalledTimes(1)
  })

  it('handles keyboard events when clickable', () => {
    const handleClick = vi.fn()
    render(<Logo clickable={true} onClick={handleClick} />)
    
    const logoButton = screen.getByRole('button')
    
    // Test Enter key
    fireEvent.keyDown(logoButton, { key: 'Enter' })
    expect(handleClick).toHaveBeenCalledTimes(1)
    
    // Test Space key
    fireEvent.keyDown(logoButton, { key: ' ' })
    expect(handleClick).toHaveBeenCalledTimes(2)
  })

  it('does not handle click events when not clickable', () => {
    const handleClick = vi.fn()
    render(<Logo clickable={false} onClick={handleClick} />)
    
    const logoContainer = document.querySelector('.logo')
    fireEvent.click(logoContainer!)
    
    expect(handleClick).not.toHaveBeenCalled()
  })

  it('applies custom className', () => {
    const customClass = 'custom-logo-class'
    render(<Logo className={customClass} />)
    
    expect(document.querySelector('.logo')).toHaveClass(customClass)
  })

  it('has proper accessibility attributes when clickable', () => {
    render(<Logo clickable={true} />)
    
    const logoButton = screen.getByRole('button')
    expect(logoButton).toHaveAttribute('tabIndex', '0')
    expect(logoButton).toHaveAttribute('aria-label', 'Appuyez pour parler')
  })

  it('has proper accessibility attributes when not clickable', () => {
    render(<Logo clickable={false} />)
    
    const logoContainer = document.querySelector('.logo')
    expect(logoContainer).toHaveAttribute('tabIndex', '-1')
  })
})
