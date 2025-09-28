import React, { forwardRef, useState } from 'react'
import clsx from 'clsx'

export interface VoiceInterfaceProps extends React.HTMLAttributes<HTMLDivElement> {
  /**
   * Current voice interface state
   */
  state?: 'idle' | 'listening' | 'processing' | 'speaking' | 'error'
  
  /**
   * Whether the voice interface is active/enabled
   */
  active?: boolean
  
  /**
   * Current transcript text
   */
  transcript?: string
  
  /**
   * Whether to show the transcript
   */
  showTranscript?: boolean
  
  /**
   * Callback when voice recording starts
   */
  onStartListening?: () => void
  
  /**
   * Callback when voice recording stops
   */
  onStopListening?: () => void
  
  /**
   * Callback when voice interface is toggled
   */
  onToggle?: () => void
  
  /**
   * Size of the voice interface
   */
  size?: 'sm' | 'md' | 'lg'
  
  /**
   * Whether to show the voice status text
   */
  showStatus?: boolean
  
  /**
   * Custom status text
   */
  statusText?: string
}

/**
 * Voice Interface component for agricultural chatbot
 * Handles voice input/output with agricultural context styling
 */
export const VoiceInterface = forwardRef<HTMLDivElement, VoiceInterfaceProps>(
  (
    {
      state = 'idle',
      active = false,
      transcript = '',
      showTranscript = true,
      onStartListening,
      onStopListening,
      onToggle,
      size = 'md',
      showStatus = true,
      statusText,
      className,
      ...props
    },
    ref
  ) => {
    const [isRecording, setIsRecording] = useState(false)
    
    const baseClasses = 'voice-interface'
    
    const stateClasses = {
      idle: 'voice-interface-idle',
      listening: 'voice-interface-listening',
      processing: 'voice-interface-processing',
      speaking: 'voice-interface-speaking',
      error: 'voice-interface-error',
    }
    
    const sizeClasses = {
      sm: 'voice-interface-sm',
      md: 'voice-interface-md',
      lg: 'voice-interface-lg',
    }
    
    const classes = clsx(
      baseClasses,
      stateClasses[state],
      sizeClasses[size],
      {
        'voice-interface-active': active,
        'voice-interface-recording': isRecording,
      },
      className
    )
    
    const getStatusText = () => {
      if (statusText) return statusText
      
      switch (state) {
        case 'idle':
          return 'Appuyez pour parler'
        case 'listening':
          return 'Écoute en cours...'
        case 'processing':
          return 'Traitement...'
        case 'speaking':
          return 'Réponse en cours...'
        case 'error':
          return 'Erreur de reconnaissance'
        default:
          return 'Interface vocale'
      }
    }
    
    const getVoiceIcon = () => {
      switch (state) {
        case 'listening':
          return (
            <svg className="voice-icon voice-icon-listening" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z"/>
              <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z"/>
            </svg>
          )
        case 'processing':
          return (
            <svg className="voice-icon voice-icon-processing" viewBox="0 0 24 24" fill="currentColor">
              <circle cx="12" cy="12" r="3" opacity="0.3"/>
              <path d="M12 1l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 1z"/>
            </svg>
          )
        case 'speaking':
          return (
            <svg className="voice-icon voice-icon-speaking" viewBox="0 0 24 24" fill="currentColor">
              <path d="M3 9v6h4l5 5V4L7 9H3zm13.5 3c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02zM14 3.23v2.06c2.89.86 5 3.54 5 6.71s-2.11 5.85-5 6.71v2.06c4.01-.91 7-4.49 7-8.77s-2.99-7.86-7-8.77z"/>
            </svg>
          )
        case 'error':
          return (
            <svg className="voice-icon voice-icon-error" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
            </svg>
          )
        default:
          return (
            <svg className="voice-icon voice-icon-idle" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z"/>
              <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z"/>
            </svg>
          )
      }
    }
    
    const handleToggle = () => {
      if (state === 'listening') {
        setIsRecording(false)
        onStopListening?.()
      } else {
        setIsRecording(true)
        onStartListening?.()
      }
      onToggle?.()
    }
    
    return (
      <div ref={ref} className={classes} {...props}>
        {/* Voice Button */}
        <button
          className="voice-button"
          onClick={handleToggle}
          disabled={state === 'processing'}
          aria-label={getStatusText()}
        >
          <div className="voice-button-icon">
            {getVoiceIcon()}
          </div>
          {state === 'listening' && (
            <div className="voice-pulse-ring" />
          )}
        </button>
        
        {/* Status Text */}
        {showStatus && (
          <div className="voice-status">
            <span className="voice-status-text">
              {getStatusText()}
            </span>
          </div>
        )}
        
        {/* Transcript */}
        {showTranscript && transcript && (
          <div className="voice-transcript">
            <div className="voice-transcript-label">
              Transcription:
            </div>
            <div className="voice-transcript-text">
              {transcript}
            </div>
          </div>
        )}
      </div>
    )
  }
)

VoiceInterface.displayName = 'VoiceInterface'

export default VoiceInterface
