/**
 * ThemeToggle Component
 * 
 * A button that toggles between light and dark themes.
 * Shows sun icon for light mode, moon icon for dark mode.
 * Only renders if theme switching is enabled.
 * 
 * Usage:
 * ```tsx
 * <ThemeToggle />
 * ```
 */

import { Sun, Moon } from 'lucide-react';
import { useTheme } from '../../hooks/useTheme';

export function ThemeToggle() {
  const { theme, toggleTheme, isEnabled } = useTheme();
  
  // Don't render if theme switching is disabled
  if (!isEnabled) {
    return null;
  }
  
  const isDark = theme === 'dark';
  
  return (
    <button
      onClick={toggleTheme}
      className="
        relative p-2 rounded-lg
        transition-all duration-200
        hover:bg-card-hover
        focus:outline-none focus:ring-2 focus:ring-offset-2
        border border-subtle
      "
      style={{
        backgroundColor: 'var(--bg-card)',
        borderColor: 'var(--border-subtle)',
      }}
      aria-label={`Switch to ${isDark ? 'light' : 'dark'} mode`}
      title={`Switch to ${isDark ? 'light' : 'dark'} mode`}
    >
      <div className="relative w-5 h-5">
        {/* Sun icon (light mode) */}
        <Sun
          className={`
            absolute inset-0 w-5 h-5
            transition-all duration-300
            ${isDark ? 'opacity-0 rotate-90 scale-0' : 'opacity-100 rotate-0 scale-100'}
          `}
          style={{ color: 'var(--text-primary)' }}
        />
        
        {/* Moon icon (dark mode) */}
        <Moon
          className={`
            absolute inset-0 w-5 h-5
            transition-all duration-300
            ${isDark ? 'opacity-100 rotate-0 scale-100' : 'opacity-0 -rotate-90 scale-0'}
          `}
          style={{ color: 'var(--text-primary)' }}
        />
      </div>
    </button>
  );
}

