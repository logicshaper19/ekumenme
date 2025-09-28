import React, { forwardRef } from 'react'
import clsx from 'clsx'

export interface LogoProps extends React.HTMLAttributes<HTMLDivElement> {
  /**
   * Size of the logo
   */
  size?: 'sm' | 'md' | 'lg' | 'xl'
  
  /**
   * Whether to show the text alongside the logo
   */
  showText?: boolean
  
  /**
   * Text to display with the logo
   */
  text?: string
  
  /**
   * Whether the logo is clickable (for navigation)
   */
  clickable?: boolean
  
  /**
   * Callback when logo is clicked
   */
  onClick?: () => void
}

/**
 * Agricultural Chatbot Logo Component
 * Features the signature dark green parallelogram design
 */
export const Logo = forwardRef<HTMLDivElement, LogoProps>(
  (
    {
      size = 'md',
      showText = true,
      text = 'Assistant Agricole IA',
      clickable = false,
      onClick,
      className,
      ...props
    },
    ref
  ) => {
    const baseClasses = 'logo'
    
    const sizeClasses = {
      sm: 'logo-sm',
      md: 'logo-md', 
      lg: 'logo-lg',
      xl: 'logo-xl',
    }
    
    const classes = clsx(
      baseClasses,
      sizeClasses[size],
      {
        'logo-clickable': clickable,
      },
      className
    )
    
    const logoSizeClasses = {
      sm: 'w-8 h-6',
      md: 'w-12 h-9',
      lg: 'w-16 h-12',
      xl: 'w-20 h-15',
    }
    
    const textSizeClasses = {
      sm: 'text-sm',
      md: 'text-lg',
      lg: 'text-xl',
      xl: 'text-2xl',
    }
    
    const LogoIcon = () => (
      <div className={clsx('logo-icon', logoSizeClasses[size])}>
        <svg
          viewBox="0 0 80 60"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
          className="w-full h-full"
        >
          {/* Dark green parallelogram */}
          <path
            d="M10 15 L70 5 L75 25 L15 35 Z"
            fill="#14532d"
            className="logo-shape"
          />
        </svg>
      </div>
    )
    
    const handleClick = () => {
      if (clickable && onClick) {
        onClick()
      }
    }
    
    return (
      <div 
        ref={ref} 
        className={classes}
        onClick={handleClick}
        role={clickable ? 'button' : undefined}
        tabIndex={clickable ? 0 : undefined}
        onKeyDown={clickable ? (e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault()
            onClick?.()
          }
        } : undefined}
        {...props}
      >
        <LogoIcon />
        {showText && (
          <span className={clsx('logo-text', textSizeClasses[size])}>
            {text}
          </span>
        )}
      </div>
    )
  }
)

Logo.displayName = 'Logo'

export default Logo
