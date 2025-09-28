import React, { forwardRef } from 'react'
import clsx from 'clsx'

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  /**
   * Visual variant of the button
   */
  variant?: 'primary' | 'secondary' | 'success' | 'warning' | 'error' | 'outline' | 'ghost'
  
  /**
   * Size of the button
   */
  size?: 'sm' | 'md' | 'lg'
  
  /**
   * Whether the button is loading
   */
  loading?: boolean
  
  /**
   * Icon to display before the button text
   */
  leftIcon?: React.ReactNode
  
  /**
   * Icon to display after the button text
   */
  rightIcon?: React.ReactNode
  
  /**
   * Whether the button should take full width
   */
  fullWidth?: boolean
}

/**
 * Button component following agricultural design system
 */
export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      variant = 'primary',
      size = 'md',
      loading = false,
      leftIcon,
      rightIcon,
      fullWidth = false,
      className,
      children,
      disabled,
      ...props
    },
    ref
  ) => {
    const baseClasses = 'btn-agricultural'
    
    const variantClasses = {
      primary: 'btn-agricultural-primary',
      secondary: 'btn-secondary',
      success: 'btn-agricultural-success',
      warning: 'btn-agricultural-warning',
      error: 'btn-agricultural-error',
      outline: 'btn-agricultural-outline',
      ghost: 'btn-agricultural-ghost',
    }
    
    const sizeClasses = {
      sm: 'btn-sm',
      md: '',
      lg: 'btn-lg',
    }
    
    const classes = clsx(
      baseClasses,
      variantClasses[variant],
      sizeClasses[size],
      {
        'w-full': fullWidth,
        'opacity-50 cursor-not-allowed': disabled || loading,
      },
      className
    )
    
    const LoadingSpinner = () => (
      <svg
        className="animate-spin -ml-1 mr-2 h-4 w-4"
        xmlns="http://www.w3.org/2000/svg"
        fill="none"
        viewBox="0 0 24 24"
      >
        <circle
          className="opacity-25"
          cx="12"
          cy="12"
          r="10"
          stroke="currentColor"
          strokeWidth="4"
        />
        <path
          className="opacity-75"
          fill="currentColor"
          d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
        />
      </svg>
    )
    
    return (
      <button
        ref={ref}
        className={classes}
        disabled={disabled || loading}
        {...props}
      >
        {loading && <LoadingSpinner />}
        {!loading && leftIcon && <span className="mr-2">{leftIcon}</span>}
        {children}
        {!loading && rightIcon && <span className="ml-2">{rightIcon}</span>}
      </button>
    )
  }
)

Button.displayName = 'Button'

export default Button
