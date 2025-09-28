import React, { forwardRef } from 'react'
import clsx from 'clsx'

export interface AgriculturalCardProps extends React.HTMLAttributes<HTMLDivElement> {
  /**
   * The type of agricultural data being displayed
   */
  type?: 'farm-data' | 'weather' | 'regulatory' | 'crop-health' | 'planning' | 'sustainability' | 'voice-journal'
  
  /**
   * The status of the data/alert level
   */
  status?: 'healthy' | 'warning' | 'critical' | 'info'
  
  /**
   * Whether the card is interactive/clickable
   */
  interactive?: boolean
  
  /**
   * Whether the card is loading
   */
  loading?: boolean
  
  /**
   * Icon to display in the card header
   */
  icon?: React.ReactNode
  
  /**
   * Title of the card
   */
  title?: string
  
  /**
   * Subtitle or description
   */
  subtitle?: string
  
  /**
   * Main content area
   */
  children: React.ReactNode
  
  /**
   * Footer content
   */
  footer?: React.ReactNode
  
  /**
   * Whether to show the agricultural border accent
   */
  showAccent?: boolean
}

/**
 * Agricultural Card component following the adapted Sema design system
 * Specialized for agricultural data display with contextual styling
 */
export const AgriculturalCard = forwardRef<HTMLDivElement, AgriculturalCardProps>(
  (
    {
      type = 'farm-data',
      status = 'info',
      interactive = false,
      loading = false,
      icon,
      title,
      subtitle,
      children,
      footer,
      showAccent = true,
      className,
      ...props
    },
    ref
  ) => {
    const baseClasses = 'agricultural-card'
    
    const typeClasses = {
      'farm-data': 'agricultural-card-farm-data',
      'weather': 'agricultural-card-weather',
      'regulatory': 'agricultural-card-regulatory',
      'crop-health': 'agricultural-card-crop-health',
      'planning': 'agricultural-card-planning',
      'sustainability': 'agricultural-card-sustainability',
      'voice-journal': 'agricultural-card-voice-journal',
    }
    
    const statusClasses = {
      healthy: 'agricultural-card-healthy',
      warning: 'agricultural-card-warning',
      critical: 'agricultural-card-critical',
      info: 'agricultural-card-info',
    }
    
    const classes = clsx(
      baseClasses,
      typeClasses[type],
      statusClasses[status],
      {
        'agricultural-card-interactive': interactive,
        'agricultural-card-loading': loading,
        'agricultural-card-accent': showAccent,
      },
      className
    )
    
    const LoadingSpinner = () => (
      <div className="agricultural-card-loading-spinner">
        <div className="spinner h-6 w-6" />
      </div>
    )
    
    return (
      <div ref={ref} className={classes} {...props}>
        {/* Header */}
        {(title || icon || subtitle) && (
          <div className="agricultural-card-header">
            <div className="agricultural-card-header-content">
              {icon && (
                <div className="agricultural-card-icon">
                  {icon}
                </div>
              )}
              <div className="agricultural-card-title-section">
                {title && (
                  <h3 className="agricultural-card-title">
                    {title}
                  </h3>
                )}
                {subtitle && (
                  <p className="agricultural-card-subtitle">
                    {subtitle}
                  </p>
                )}
              </div>
            </div>
            {loading && <LoadingSpinner />}
          </div>
        )}
        
        {/* Body */}
        <div className="agricultural-card-body">
          {children}
        </div>
        
        {/* Footer */}
        {footer && (
          <div className="agricultural-card-footer">
            {footer}
          </div>
        )}
      </div>
    )
  }
)

AgriculturalCard.displayName = 'AgriculturalCard'

export default AgriculturalCard
