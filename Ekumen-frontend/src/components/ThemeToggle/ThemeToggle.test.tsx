/**
 * ThemeToggle Component Tests
 * 
 * Tests for the theme toggle button component
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { ThemeToggle } from './ThemeToggle';
import { useThemeStore } from '../../stores/themeStore';

// Mock the theme config to enable theme switching
vi.mock('../../config/theme.config', () => ({
  default: {
    enabled: true,
    defaultTheme: 'light',
    storageKey: 'ekumen-theme',
    dataAttribute: 'data-theme'
  }
}));

describe('ThemeToggle Component', () => {
  beforeEach(() => {
    // Clear localStorage and reset store
    localStorage.clear();
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

  it('should render when theme switching is enabled', () => {
    render(<ThemeToggle />);
    
    const button = screen.getByRole('button');
    expect(button).toBeInTheDocument();
  });

  it('should have accessible label', () => {
    render(<ThemeToggle />);
    
    const button = screen.getByRole('button');
    expect(button).toHaveAttribute('aria-label');
  });

  it('should show sun icon in light mode', () => {
    useThemeStore.setState({ theme: 'light' });
    render(<ThemeToggle />);
    
    const button = screen.getByRole('button');
    expect(button).toHaveAttribute('aria-label', 'Switch to dark mode');
  });

  it('should show moon icon in dark mode', () => {
    useThemeStore.setState({ theme: 'dark' });
    render(<ThemeToggle />);
    
    const button = screen.getByRole('button');
    expect(button).toHaveAttribute('aria-label', 'Switch to light mode');
  });

  it('should toggle theme when clicked', () => {
    render(<ThemeToggle />);
    
    const button = screen.getByRole('button');
    
    // Initial theme is light
    expect(useThemeStore.getState().theme).toBe('light');
    
    // Click to toggle
    fireEvent.click(button);
    
    // Theme should be dark
    expect(useThemeStore.getState().theme).toBe('dark');
  });

  it('should update DOM attribute when toggled', () => {
    render(<ThemeToggle />);
    
    const button = screen.getByRole('button');
    
    fireEvent.click(button);
    
    expect(document.documentElement.getAttribute('data-theme')).toBe('dark');
  });

  it('should have title attribute for tooltip', () => {
    render(<ThemeToggle />);
    
    const button = screen.getByRole('button');
    expect(button).toHaveAttribute('title');
  });

  it('should apply theme-aware styles', () => {
    render(<ThemeToggle />);
    
    const button = screen.getByRole('button');
    
    // Should have inline styles for theme variables
    expect(button).toHaveStyle({ backgroundColor: 'var(--bg-card)' });
    expect(button).toHaveStyle({ borderColor: 'var(--border-subtle)' });
  });

  it('should toggle multiple times', () => {
    render(<ThemeToggle />);
    
    const button = screen.getByRole('button');
    
    // Toggle to dark
    fireEvent.click(button);
    expect(useThemeStore.getState().theme).toBe('dark');
    
    // Toggle back to light
    fireEvent.click(button);
    expect(useThemeStore.getState().theme).toBe('light');
    
    // Toggle to dark again
    fireEvent.click(button);
    expect(useThemeStore.getState().theme).toBe('dark');
  });
});

describe('ThemeToggle - Feature Flag Disabled', () => {
  beforeEach(() => {
    // Mock theme config with disabled flag
    vi.resetModules();
    vi.doMock('../../config/theme.config', () => ({
      default: {
        enabled: false,
        defaultTheme: 'light',
        storageKey: 'ekumen-theme',
        dataAttribute: 'data-theme'
      }
    }));
  });

  it('should not render when theme switching is disabled', () => {
    const { container } = render(<ThemeToggle />);
    
    // Component should render null
    expect(container.firstChild).toBeNull();
  });
});

