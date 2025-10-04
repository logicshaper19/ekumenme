/**
 * Centralized Theme Configuration
 * 
 * Single source of truth for all theme-related settings.
 * Provides type safety and consistent naming across the application.
 */

export type Theme = 'light' | 'dark';

export interface ThemeConfig {
  /** Whether theme switching is enabled (controlled by feature flag) */
  enabled: boolean;
  /** Default theme to use when no preference is set */
  defaultTheme: Theme;
  /** localStorage key for persisting theme preference */
  storageKey: string;
  /** HTML data attribute used to apply theme */
  dataAttribute: string;
}

const THEME_CONFIG: ThemeConfig = {
  enabled: import.meta.env.VITE_THEME_SWITCH_ENABLED === 'true',
  defaultTheme: 'light' as const, // Default to light theme
  storageKey: 'ekumen-theme',
  dataAttribute: 'data-theme'
} as const;

export default THEME_CONFIG;

