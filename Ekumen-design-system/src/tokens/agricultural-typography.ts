// Agricultural Chatbot Design System - Typography Tokens
// Adapted from Sema design system for agricultural context

export const typography = {
  // Font families
  fontFamily: {
    sans: [
      'Inter',
      'system-ui',
      '-apple-system',
      'BlinkMacSystemFont',
      '"Segoe UI"',
      'Roboto',
      '"Helvetica Neue"',
      'Arial',
      '"Noto Sans"',
      'sans-serif',
    ],
    mono: [
      'JetBrains Mono',
      'Menlo',
      'Monaco',
      'Consolas',
      '"Liberation Mono"',
      '"Courier New"',
      'monospace',
    ],
    display: [
      'Inter',
      'system-ui',
      '-apple-system',
      'BlinkMacSystemFont',
      '"Segoe UI"',
      'Roboto',
      '"Helvetica Neue"',
      'Arial',
      'sans-serif',
    ],
  },

  // Font sizes with agricultural context
  fontSize: {
    xs: ['0.75rem', { lineHeight: '1rem' }],      // 12px - Small labels, badges
    sm: ['0.875rem', { lineHeight: '1.25rem' }],   // 14px - Body text, form labels
    base: ['1rem', { lineHeight: '1.5rem' }],      // 16px - Default body text
    lg: ['1.125rem', { lineHeight: '1.75rem' }],   // 18px - Large body text
    xl: ['1.25rem', { lineHeight: '1.75rem' }],    // 20px - Small headings
    '2xl': ['1.5rem', { lineHeight: '2rem' }],     // 24px - Section headings
    '3xl': ['1.875rem', { lineHeight: '2.25rem' }], // 30px - Page headings
    '4xl': ['2.25rem', { lineHeight: '2.5rem' }],  // 36px - Large headings
    '5xl': ['3rem', { lineHeight: '1' }],          // 48px - Hero headings
    '6xl': ['3.75rem', { lineHeight: '1' }],       // 60px - Display headings
    '7xl': ['4.5rem', { lineHeight: '1' }],        // 72px - Large display
    '8xl': ['6rem', { lineHeight: '1' }],          // 96px - Extra large display
    '9xl': ['8rem', { lineHeight: '1' }],          // 128px - Ultra large display
  },

  // Font weights
  fontWeight: {
    thin: '100',
    extralight: '200',
    light: '300',
    normal: '400',
    medium: '500',
    semibold: '600',
    bold: '700',
    extrabold: '800',
    black: '900',
  },

  // Letter spacing
  letterSpacing: {
    tighter: '-0.05em',
    tight: '-0.025em',
    normal: '0em',
    wide: '0.025em',
    wider: '0.05em',
    widest: '0.1em',
  },

  // Line heights
  lineHeight: {
    none: '1',
    tight: '1.25',
    snug: '1.375',
    normal: '1.5',
    relaxed: '1.625',
    loose: '2',
  },
} as const

// Typography scale for agricultural context
export const typographyScale = {
  // Agent-specific typography
  agentName: {
    fontSize: typography.fontSize.lg,
    fontWeight: typography.fontWeight.semibold,
    lineHeight: typography.lineHeight.tight,
    color: 'text-gray-900',
  },

  agentDescription: {
    fontSize: typography.fontSize.sm,
    fontWeight: typography.fontWeight.normal,
    lineHeight: typography.lineHeight.normal,
    color: 'text-gray-600',
  },

  // Chat message typography
  chatMessage: {
    fontSize: typography.fontSize.base,
    fontWeight: typography.fontWeight.normal,
    lineHeight: typography.lineHeight.relaxed,
    color: 'text-gray-800',
  },

  chatTimestamp: {
    fontSize: typography.fontSize.xs,
    fontWeight: typography.fontWeight.normal,
    lineHeight: typography.lineHeight.normal,
    color: 'text-gray-500',
  },

  // Voice interface typography
  voiceStatus: {
    fontSize: typography.fontSize.sm,
    fontWeight: typography.fontWeight.medium,
    lineHeight: typography.lineHeight.normal,
    color: 'text-gray-700',
  },

  voiceTranscript: {
    fontSize: typography.fontSize.base,
    fontWeight: typography.fontWeight.normal,
    lineHeight: typography.lineHeight.relaxed,
    color: 'text-gray-800',
  },

  // Data display typography
  dataLabel: {
    fontSize: typography.fontSize.sm,
    fontWeight: typography.fontWeight.medium,
    lineHeight: typography.lineHeight.normal,
    color: 'text-gray-600',
  },

  dataValue: {
    fontSize: typography.fontSize.lg,
    fontWeight: typography.fontWeight.semibold,
    lineHeight: typography.lineHeight.tight,
    color: 'text-gray-900',
  },

  dataUnit: {
    fontSize: typography.fontSize.sm,
    fontWeight: typography.fontWeight.normal,
    lineHeight: typography.lineHeight.normal,
    color: 'text-gray-500',
  },

  // Weather data typography
  weatherTemp: {
    fontSize: typography.fontSize['3xl'],
    fontWeight: typography.fontWeight.bold,
    lineHeight: typography.lineHeight.none,
    color: 'text-gray-900',
  },

  weatherCondition: {
    fontSize: typography.fontSize.base,
    fontWeight: typography.fontWeight.medium,
    lineHeight: typography.lineHeight.normal,
    color: 'text-gray-700',
  },

  // Regulatory typography
  regulationTitle: {
    fontSize: typography.fontSize.lg,
    fontWeight: typography.fontWeight.semibold,
    lineHeight: typography.lineHeight.tight,
    color: 'text-gray-900',
  },

  regulationText: {
    fontSize: typography.fontSize.sm,
    fontWeight: typography.fontWeight.normal,
    lineHeight: typography.lineHeight.relaxed,
    color: 'text-gray-700',
  },

  // Alert typography
  alertTitle: {
    fontSize: typography.fontSize.base,
    fontWeight: typography.fontWeight.semibold,
    lineHeight: typography.lineHeight.tight,
  },

  alertMessage: {
    fontSize: typography.fontSize.sm,
    fontWeight: typography.fontWeight.normal,
    lineHeight: typography.lineHeight.normal,
  },

  // Navigation typography
  navItem: {
    fontSize: typography.fontSize.sm,
    fontWeight: typography.fontWeight.medium,
    lineHeight: typography.lineHeight.normal,
    color: 'text-gray-700',
  },

  navItemActive: {
    fontSize: typography.fontSize.sm,
    fontWeight: typography.fontWeight.semibold,
    lineHeight: typography.lineHeight.normal,
    color: 'text-primary-700',
  },

  // Button typography
  buttonText: {
    fontSize: typography.fontSize.sm,
    fontWeight: typography.fontWeight.medium,
    lineHeight: typography.lineHeight.none,
  },

  buttonTextLarge: {
    fontSize: typography.fontSize.base,
    fontWeight: typography.fontWeight.medium,
    lineHeight: typography.lineHeight.none,
  },

  // Form typography
  formLabel: {
    fontSize: typography.fontSize.sm,
    fontWeight: typography.fontWeight.medium,
    lineHeight: typography.lineHeight.normal,
    color: 'text-gray-700',
  },

  formInput: {
    fontSize: typography.fontSize.sm,
    fontWeight: typography.fontWeight.normal,
    lineHeight: typography.lineHeight.normal,
    color: 'text-gray-900',
  },

  formError: {
    fontSize: typography.fontSize.xs,
    fontWeight: typography.fontWeight.normal,
    lineHeight: typography.lineHeight.normal,
    color: 'text-error-600',
  },

  formHelp: {
    fontSize: typography.fontSize.xs,
    fontWeight: typography.fontWeight.normal,
    lineHeight: typography.lineHeight.normal,
    color: 'text-gray-500',
  },
} as const

// Type definitions
export type FontFamilyKey = keyof typeof typography.fontFamily
export type FontSizeKey = keyof typeof typography.fontSize
export type FontWeightKey = keyof typeof typography.fontWeight
export type LetterSpacingKey = keyof typeof typography.letterSpacing
export type LineHeightKey = keyof typeof typography.lineHeight
export type TypographyScaleKey = keyof typeof typographyScale
