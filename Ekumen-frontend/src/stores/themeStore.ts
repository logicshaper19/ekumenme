/**
 * Theme Store - Zustand State Management
 * 
 * Combines Zustand for state management with CSS variables for visual rendering.
 * Provides automatic localStorage persistence and system preference detection.
 * 
 * Benefits:
 * - State Management: Zustand handles React state and persistence
 * - Visual Updates: CSS variables handle actual styling
 * - Performance: CSS variables update instantly without React re-renders
 * - Developer Experience: Simple API with useTheme() hook
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import THEME_CONFIG, { Theme } from '../config/theme.config';

interface ThemeState {
  /** Current theme ('light' or 'dark') */
  theme: Theme;
  
  /** Set the theme and update the DOM */
  setTheme: (theme: Theme) => void;
  
  /** Toggle between light and dark themes */
  toggleTheme: () => void;
  
  /** Initialize theme from localStorage or system preference */
  initTheme: () => void;
  
  /** Check if theme switching is enabled */
  isEnabled: () => boolean;
}

export const useThemeStore = create<ThemeState>()(
  persist(
    (set, get) => ({
      theme: THEME_CONFIG.defaultTheme,
      
      setTheme: (theme: Theme) => {
        // Only allow theme changes if feature is enabled
        if (!THEME_CONFIG.enabled) {
          console.warn('Theme switching is disabled. Set VITE_THEME_SWITCH_ENABLED=true to enable.');
          return;
        }
        
        // Update DOM attribute for CSS variables
        document.documentElement.setAttribute(THEME_CONFIG.dataAttribute, theme);
        
        // Update Zustand state
        set({ theme });
        
        console.log(`Theme changed to: ${theme}`);
      },
      
      toggleTheme: () => {
        const currentTheme = get().theme;
        const newTheme: Theme = currentTheme === 'light' ? 'dark' : 'light';
        get().setTheme(newTheme);
      },
      
      initTheme: () => {
        // Check if theme switching is enabled
        if (!THEME_CONFIG.enabled) {
          // Force light theme if disabled
          document.documentElement.setAttribute(THEME_CONFIG.dataAttribute, 'light');
          set({ theme: 'light' });
          return;
        }
        
        // Try to get stored theme from localStorage
        const stored = localStorage.getItem(THEME_CONFIG.storageKey);
        
        if (stored) {
          try {
            const parsedState = JSON.parse(stored);
            const storedTheme = parsedState?.state?.theme;
            
            if (storedTheme === 'light' || storedTheme === 'dark') {
              get().setTheme(storedTheme);
              return;
            }
          } catch (error) {
            console.error('Failed to parse stored theme:', error);
          }
        }
        
        // Fall back to default theme (light)
        get().setTheme(THEME_CONFIG.defaultTheme);
        console.log(`Initialized theme to default: ${THEME_CONFIG.defaultTheme}`);
      },
      
      isEnabled: () => THEME_CONFIG.enabled,
    }),
    {
      name: THEME_CONFIG.storageKey,
      // Only persist the theme value
      partialize: (state) => ({ theme: state.theme }),
    }
  )
);

/**
 * Listen for system theme changes
 * Updates theme automatically if user changes their OS preference
 */
if (typeof window !== 'undefined' && window.matchMedia) {
  try {
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');

    mediaQuery.addEventListener('change', (e) => {
      const store = useThemeStore.getState();

      // Only auto-update if theme switching is enabled
      // and user hasn't manually set a preference
      if (store.isEnabled()) {
        const hasManualPreference = localStorage.getItem(THEME_CONFIG.storageKey);

        if (!hasManualPreference) {
          const newTheme: Theme = e.matches ? 'dark' : 'light';
          store.setTheme(newTheme);
          console.log(`System theme changed to: ${newTheme}`);
        }
      }
    });
  } catch (error) {
    // Silently fail if matchMedia is not available (e.g., in tests)
    console.warn('matchMedia not available:', error);
  }
}

