// Agricultural Chatbot Design System
// Adapted from Sema design system for agricultural context

// Export all design tokens
export * from './tokens/agricultural-colors'
export * from './tokens/agricultural-typography'

// Export all components
export * from './components/AgriculturalCard'
export * from './components/VoiceInterface'
export * from './components/Logo'

// Re-export commonly used tokens for convenience
export { colors, semanticColors } from './tokens/agricultural-colors'
export { typography, typographyScale } from './tokens/agricultural-typography'

// Combined token object for easy access
import { colors } from './tokens/agricultural-colors'
import { typography } from './tokens/agricultural-typography'

export const agriculturalTokens = {
  colors,
  typography,
} as const

// Border radius tokens (inherited from Sema)
export const borderRadius = {
  none: '0',
  sm: '0.125rem',      // 2px
  DEFAULT: '0.25rem',   // 4px
  md: '0.375rem',      // 6px
  lg: '0.5rem',        // 8px
  xl: '0.75rem',       // 12px
  '2xl': '1rem',       // 16px
  '3xl': '1.5rem',     // 24px
  full: '9999px',
} as const

// Animation tokens (inherited from Sema with agricultural additions)
export const animations = {
  duration: {
    75: '75ms',
    100: '100ms',
    150: '150ms',
    200: '200ms',
    300: '300ms',
    500: '500ms',
    700: '700ms',
    1000: '1000ms',
  },
  
  easing: {
    linear: 'linear',
    in: 'cubic-bezier(0.4, 0, 1, 1)',
    out: 'cubic-bezier(0, 0, 0.2, 1)',
    'in-out': 'cubic-bezier(0.4, 0, 0.2, 1)',
  },
  
  keyframes: {
    fadeIn: {
      '0%': { opacity: '0' },
      '100%': { opacity: '1' },
    },
    fadeOut: {
      '0%': { opacity: '1' },
      '100%': { opacity: '0' },
    },
    slideUp: {
      '0%': { transform: 'translateY(10px)', opacity: '0' },
      '100%': { transform: 'translateY(0)', opacity: '1' },
    },
    slideDown: {
      '0%': { transform: 'translateY(-10px)', opacity: '0' },
      '100%': { transform: 'translateY(0)', opacity: '1' },
    },
    slideLeft: {
      '0%': { transform: 'translateX(10px)', opacity: '0' },
      '100%': { transform: 'translateX(0)', opacity: '1' },
    },
    slideRight: {
      '0%': { transform: 'translateX(-10px)', opacity: '0' },
      '100%': { transform: 'translateX(0)', opacity: '1' },
    },
    scale: {
      '0%': { transform: 'scale(0.95)', opacity: '0' },
      '100%': { transform: 'scale(1)', opacity: '1' },
    },
    spin: {
      '0%': { transform: 'rotate(0deg)' },
      '100%': { transform: 'rotate(360deg)' },
    },
    pulse: {
      '0%, 100%': { opacity: '1' },
      '50%': { opacity: '0.5' },
    },
    bounce: {
      '0%, 100%': { 
        transform: 'translateY(-25%)',
        animationTimingFunction: 'cubic-bezier(0.8, 0, 1, 1)',
      },
      '50%': { 
        transform: 'translateY(0)',
        animationTimingFunction: 'cubic-bezier(0, 0, 0.2, 1)',
      },
    },
    // Agricultural-specific animations
    grow: {
      '0%': { transform: 'scale(0.8)', opacity: '0' },
      '100%': { transform: 'scale(1)', opacity: '1' },
    },
    harvest: {
      '0%': { transform: 'translateY(0) rotate(0deg)' },
      '50%': { transform: 'translateY(-10px) rotate(5deg)' },
      '100%': { transform: 'translateY(0) rotate(0deg)' },
    },
    weather: {
      '0%': { transform: 'translateX(0)' },
      '50%': { transform: 'translateX(5px)' },
      '100%': { transform: 'translateX(0)' },
    },
  },
  
  presets: {
    'fade-in': {
      animation: 'fadeIn 0.5s ease-in-out',
    },
    'slide-up': {
      animation: 'slideUp 0.3s ease-out',
    },
    'slide-down': {
      animation: 'slideDown 0.3s ease-out',
    },
    'pulse-slow': {
      animation: 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
    },
    'spin': {
      animation: 'spin 1s linear infinite',
    },
    'grow': {
      animation: 'grow 0.4s ease-out',
    },
    'harvest': {
      animation: 'harvest 0.6s ease-in-out',
    },
    'weather': {
      animation: 'weather 2s ease-in-out infinite',
    },
  },
} as const

// Breakpoint tokens (inherited from Sema)
export const breakpoints = {
  xs: '475px',
  sm: '640px',
  md: '768px',
  lg: '1024px',
  xl: '1280px',
  '2xl': '1536px',
} as const

// Z-index tokens (inherited from Sema with agricultural additions)
export const zIndex = {
  auto: 'auto',
  0: '0',
  10: '10',
  20: '20',
  30: '30',
  40: '40',
  50: '50',
  dropdown: '1000',
  sticky: '1020',
  fixed: '1030',
  modal: '1040',
  popover: '1050',
  tooltip: '1060',
  toast: '1070',
  overlay: '1080',
  voiceInterface: '1090',
  chatInterface: '1100',
} as const

// Opacity tokens (inherited from Sema)
export const opacity = {
  0: '0',
  5: '0.05',
  10: '0.1',
  20: '0.2',
  25: '0.25',
  30: '0.3',
  40: '0.4',
  50: '0.5',
  60: '0.6',
  70: '0.7',
  75: '0.75',
  80: '0.8',
  90: '0.9',
  95: '0.95',
  100: '1',
} as const

// Type definitions for all tokens
export type BorderRadiusKey = keyof typeof borderRadius
export type AnimationDuration = keyof typeof animations.duration
export type AnimationEasing = keyof typeof animations.easing
export type AnimationKeyframe = keyof typeof animations.keyframes
export type AnimationPreset = keyof typeof animations.presets
export type Breakpoint = keyof typeof breakpoints
export type ZIndexKey = keyof typeof zIndex
export type OpacityKey = keyof typeof opacity
