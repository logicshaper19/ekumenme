/**
 * Theme Store Tests
 * 
 * Tests for the Zustand theme store including:
 * - Initial state
 * - Theme switching
 * - localStorage persistence
 * - System preference detection
 * - Feature flag behavior
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { useThemeStore } from './themeStore';

describe('ThemeStore', () => {
  // Save original values
  const originalLocalStorage = global.localStorage;
  const originalMatchMedia = global.matchMedia;
  
  beforeEach(() => {
    // Clear localStorage before each test
    localStorage.clear();
    
    // Reset store state
    useThemeStore.setState({ theme: 'light' });
    
    // Mock matchMedia
    Object.defineProperty(window, 'matchMedia', {
      writable: true,
      value: vi.fn().mockImplementation(query => ({
        matches: false,
        media: query,
        onchange: null,
        addListener: vi.fn(),
        removeListener: vi.fn(),
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        dispatchEvent: vi.fn(),
      })),
    });
  });
  
  afterEach(() => {
    // Restore original values
    global.localStorage = originalLocalStorage;
    global.matchMedia = originalMatchMedia;
  });

  describe('Initial State', () => {
    it('should have light theme as default', () => {
      const { theme } = useThemeStore.getState();
      expect(theme).toBe('light');
    });
  });

  describe('setTheme', () => {
    it('should update theme state', () => {
      const { setTheme } = useThemeStore.getState();
      
      setTheme('dark');
      
      const { theme } = useThemeStore.getState();
      expect(theme).toBe('dark');
    });

    it('should update DOM attribute', () => {
      const { setTheme } = useThemeStore.getState();
      
      setTheme('dark');
      
      expect(document.documentElement.getAttribute('data-theme')).toBe('dark');
    });

    it('should persist to localStorage', () => {
      const { setTheme } = useThemeStore.getState();
      
      setTheme('dark');
      
      const stored = localStorage.getItem('ekumen-theme');
      expect(stored).toBeTruthy();
      
      const parsed = JSON.parse(stored!);
      expect(parsed.state.theme).toBe('dark');
    });
  });

  describe('toggleTheme', () => {
    it('should toggle from light to dark', () => {
      const { toggleTheme } = useThemeStore.getState();
      
      toggleTheme();
      
      const { theme } = useThemeStore.getState();
      expect(theme).toBe('dark');
    });

    it('should toggle from dark to light', () => {
      const { setTheme, toggleTheme } = useThemeStore.getState();
      
      setTheme('dark');
      toggleTheme();
      
      const { theme } = useThemeStore.getState();
      expect(theme).toBe('light');
    });

    it('should update DOM on toggle', () => {
      const { toggleTheme } = useThemeStore.getState();
      
      toggleTheme();
      expect(document.documentElement.getAttribute('data-theme')).toBe('dark');
      
      toggleTheme();
      expect(document.documentElement.getAttribute('data-theme')).toBe('light');
    });
  });

  describe('initTheme', () => {
    it('should use stored theme if available', () => {
      // Set up localStorage with dark theme
      localStorage.setItem('ekumen-theme', JSON.stringify({
        state: { theme: 'dark' },
        version: 0
      }));
      
      const { initTheme } = useThemeStore.getState();
      initTheme();
      
      const { theme } = useThemeStore.getState();
      expect(theme).toBe('dark');
    });

    it('should use system preference if no stored theme', () => {
      // Mock system preference for dark mode
      Object.defineProperty(window, 'matchMedia', {
        writable: true,
        value: vi.fn().mockImplementation(query => ({
          matches: query === '(prefers-color-scheme: dark)',
          media: query,
          onchange: null,
          addListener: vi.fn(),
          removeListener: vi.fn(),
          addEventListener: vi.fn(),
          removeEventListener: vi.fn(),
          dispatchEvent: vi.fn(),
        })),
      });
      
      const { initTheme } = useThemeStore.getState();
      initTheme();
      
      const { theme } = useThemeStore.getState();
      expect(theme).toBe('dark');
    });

    it('should default to light if no preference', () => {
      const { initTheme } = useThemeStore.getState();
      initTheme();
      
      const { theme } = useThemeStore.getState();
      expect(theme).toBe('light');
    });
  });

  describe('isEnabled', () => {
    it('should return feature flag status', () => {
      const { isEnabled } = useThemeStore.getState();
      
      // This depends on the environment variable
      // In tests, it should be true by default
      expect(typeof isEnabled()).toBe('boolean');
    });
  });

  describe('Persistence', () => {
    it('should persist theme changes', () => {
      const { setTheme } = useThemeStore.getState();
      
      setTheme('dark');
      
      const stored = localStorage.getItem('ekumen-theme');
      expect(stored).toBeTruthy();
      
      const parsed = JSON.parse(stored!);
      expect(parsed.state.theme).toBe('dark');
    });

    it('should restore theme from localStorage', () => {
      // Manually set localStorage
      localStorage.setItem('ekumen-theme', JSON.stringify({
        state: { theme: 'dark' },
        version: 0
      }));
      
      const { initTheme } = useThemeStore.getState();
      initTheme();
      
      const { theme } = useThemeStore.getState();
      expect(theme).toBe('dark');
    });
  });

  describe('Error Handling', () => {
    it('should handle invalid stored theme gracefully', () => {
      localStorage.setItem('ekumen-theme', 'invalid json');
      
      const { initTheme } = useThemeStore.getState();
      
      // Should not throw
      expect(() => initTheme()).not.toThrow();
      
      // Should fall back to system preference or default
      const { theme } = useThemeStore.getState();
      expect(['light', 'dark']).toContain(theme);
    });

    it('should handle missing theme in stored data', () => {
      localStorage.setItem('ekumen-theme', JSON.stringify({
        state: {},
        version: 0
      }));
      
      const { initTheme } = useThemeStore.getState();
      initTheme();
      
      // Should fall back to system preference or default
      const { theme } = useThemeStore.getState();
      expect(['light', 'dark']).toContain(theme);
    });
  });

  describe('DOM Updates', () => {
    it('should set data-theme attribute on document element', () => {
      const { setTheme } = useThemeStore.getState();
      
      setTheme('dark');
      
      expect(document.documentElement.getAttribute('data-theme')).toBe('dark');
    });

    it('should update data-theme attribute when theme changes', () => {
      const { setTheme } = useThemeStore.getState();
      
      setTheme('dark');
      expect(document.documentElement.getAttribute('data-theme')).toBe('dark');
      
      setTheme('light');
      expect(document.documentElement.getAttribute('data-theme')).toBe('light');
    });
  });
});

