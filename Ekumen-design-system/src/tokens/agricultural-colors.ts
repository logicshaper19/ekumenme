// Agricultural Chatbot Design System - Color Tokens
// Adapted from Sema design system for agricultural context

export const colors = {
  // Primary agricultural green palette
  primary: {
    50: '#f0fdf4',   // Light green background
    100: '#dcfce7',  // Very light green
    200: '#bbf7d0',  // Light green
    300: '#86efac',  // Medium light green
    400: '#4ade80',  // Medium green
    500: '#22c55e',  // Primary green (main brand)
    600: '#16a34a',  // Dark green
    700: '#15803d',  // Darker green
    800: '#166534',  // Very dark green
    900: '#14532d',  // Darkest green
    950: '#052e16',  // Ultra dark green
  },

  // Earth tones for agricultural context
  earth: {
    50: '#fafaf9',   // Stone 50
    100: '#f5f5f4',  // Stone 100
    200: '#e7e5e4',  // Stone 200
    300: '#d6d3d1',  // Stone 300
    400: '#a8a29e',  // Stone 400
    500: '#78716c',  // Stone 500
    600: '#57534e',  // Stone 600
    700: '#44403c',  // Stone 700
    800: '#292524',  // Stone 800
    900: '#1c1917',  // Stone 900
    950: '#0c0a09',  // Stone 950
  },

  // Success colors (healthy crops, good conditions)
  success: {
    50: '#f0fdf4',
    100: '#dcfce7',
    200: '#bbf7d0',
    300: '#86efac',
    400: '#4ade80',
    500: '#22c55e',
    600: '#16a34a',
    700: '#15803d',
    800: '#166534',
    900: '#14532d',
  },

  // Warning colors (caution, attention needed)
  warning: {
    50: '#fffbeb',
    100: '#fef3c7',
    200: '#fde68a',
    300: '#fcd34d',
    400: '#fbbf24',
    500: '#f59e0b',
    600: '#d97706',
    700: '#b45309',
    800: '#92400e',
    900: '#78350f',
  },

  // Error colors (problems, alerts)
  error: {
    50: '#fef2f2',
    100: '#fee2e2',
    200: '#fecaca',
    300: '#fca5a5',
    400: '#f87171',
    500: '#ef4444',
    600: '#dc2626',
    700: '#b91c1c',
    800: '#991b1b',
    900: '#7f1d1d',
  },

  // Info colors (information, data)
  info: {
    50: '#eff6ff',
    100: '#dbeafe',
    200: '#bfdbfe',
    300: '#93c5fd',
    400: '#60a5fa',
    500: '#3b82f6',
    600: '#2563eb',
    700: '#1d4ed8',
    800: '#1e40af',
    900: '#1e3a8a',
  },

  // Neutral grays
  gray: {
    50: '#f9fafb',
    100: '#f3f4f6',
    200: '#e5e7eb',
    300: '#d1d5db',
    400: '#9ca3af',
    500: '#6b7280',
    600: '#4b5563',
    700: '#374151',
    800: '#1f2937',
    900: '#111827',
    950: '#030712',
  },

  // Weather-specific colors
  weather: {
    sunny: '#fbbf24',      // Yellow for sunny weather
    cloudy: '#9ca3af',     // Gray for cloudy weather
    rainy: '#3b82f6',      // Blue for rain
    stormy: '#7c3aed',     // Purple for storms
    snowy: '#f8fafc',      // White for snow
    foggy: '#d1d5db',      // Light gray for fog
  },

  // Crop-specific colors
  crops: {
    wheat: '#fbbf24',      // Golden wheat
    corn: '#f59e0b',       // Corn yellow
    soy: '#16a34a',        // Soy green
    potato: '#f3f4f6',     // Potato white
    tomato: '#ef4444',     // Tomato red
    lettuce: '#22c55e',    // Lettuce green
    carrot: '#f97316',     // Carrot orange
    beet: '#be185d',       // Beet purple
  },

  // Soil colors
  soil: {
    clay: '#92400e',       // Clay brown
    sand: '#fbbf24',       // Sandy yellow
    loam: '#a3a3a3',       // Loam gray
    peat: '#451a03',       // Peat dark brown
  },
} as const

// Semantic color mappings for agricultural context
export const semanticColors = {
  // Agent-specific colors
  farmData: colors.info,
  regulatory: colors.warning,
  weather: colors.weather,
  cropHealth: colors.success,
  planning: colors.primary,
  sustainability: colors.earth,

  // Status colors
  healthy: colors.success[500],
  warning: colors.warning[500],
  critical: colors.error[500],
  info: colors.info[500],

  // Weather conditions
  optimal: colors.success[400],
  caution: colors.warning[400],
  dangerous: colors.error[400],

  // Crop health
  excellent: colors.success[600],
  good: colors.success[400],
  fair: colors.warning[400],
  poor: colors.error[400],

  // Regulatory status
  approved: colors.success[500],
  pending: colors.warning[500],
  rejected: colors.error[500],
  restricted: colors.error[600],

  // Voice interface states
  listening: colors.info[500],
  processing: colors.warning[500],
  speaking: colors.success[500],
  error: colors.error[500],
} as const

// Type definitions
export type ColorKey = keyof typeof colors
export type SemanticColorKey = keyof typeof semanticColors
export type PrimaryColorShade = keyof typeof colors.primary
export type WeatherColorKey = keyof typeof colors.weather
export type CropColorKey = keyof typeof colors.crops
export type SoilColorKey = keyof typeof colors.soil
