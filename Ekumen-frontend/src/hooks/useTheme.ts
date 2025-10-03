/**
 * useTheme Hook - Convenience wrapper for theme store
 * 
 * Provides a simple API for components to access and control theme.
 * 
 * Usage:
 * ```tsx
 * const { theme, setTheme, toggleTheme, isEnabled } = useTheme();
 * 
 * // Check current theme
 * if (theme === 'dark') { ... }
 * 
 * // Change theme
 * setTheme('dark');
 * 
 * // Toggle theme
 * toggleTheme();
 * 
 * // Check if theme switching is enabled
 * if (isEnabled) { ... }
 * ```
 */

import { useEffect } from 'react';
import { useThemeStore } from '../stores/themeStore';
import { Theme } from '../config/theme.config';

export interface UseThemeReturn {
  /** Current theme ('light' or 'dark') */
  theme: Theme;
  
  /** Set the theme */
  setTheme: (theme: Theme) => void;
  
  /** Toggle between light and dark themes */
  toggleTheme: () => void;
  
  /** Whether theme switching is enabled */
  isEnabled: boolean;
}

/**
 * Hook to access and control the application theme
 */
export function useTheme(): UseThemeReturn {
  const { theme, setTheme, toggleTheme, initTheme, isEnabled } = useThemeStore();
  
  // Initialize theme on mount
  useEffect(() => {
    initTheme();
  }, [initTheme]);
  
  return {
    theme,
    setTheme,
    toggleTheme,
    isEnabled: isEnabled(),
  };
}

