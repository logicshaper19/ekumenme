/**
 * useTheme Hook Tests
 * 
 * Tests for the useTheme convenience hook
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useTheme } from './useTheme';
import { useThemeStore } from '../stores/themeStore';

describe('useTheme Hook', () => {
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

  it('should return current theme', () => {
    const { result } = renderHook(() => useTheme());
    
    expect(result.current.theme).toBe('light');
  });

  it('should provide setTheme function', () => {
    const { result } = renderHook(() => useTheme());
    
    expect(typeof result.current.setTheme).toBe('function');
  });

  it('should provide toggleTheme function', () => {
    const { result } = renderHook(() => useTheme());
    
    expect(typeof result.current.toggleTheme).toBe('function');
  });

  it('should provide isEnabled flag', () => {
    const { result } = renderHook(() => useTheme());
    
    expect(typeof result.current.isEnabled).toBe('boolean');
  });

  it('should update theme when setTheme is called', () => {
    const { result } = renderHook(() => useTheme());
    
    act(() => {
      result.current.setTheme('dark');
    });
    
    expect(result.current.theme).toBe('dark');
  });

  it('should toggle theme when toggleTheme is called', () => {
    const { result } = renderHook(() => useTheme());
    
    act(() => {
      result.current.toggleTheme();
    });
    
    expect(result.current.theme).toBe('dark');
    
    act(() => {
      result.current.toggleTheme();
    });
    
    expect(result.current.theme).toBe('light');
  });

  it('should initialize theme on mount', () => {
    // Set up localStorage with dark theme
    localStorage.setItem('ekumen-theme', JSON.stringify({
      state: { theme: 'dark' },
      version: 0
    }));
    
    const { result } = renderHook(() => useTheme());
    
    // Theme should be initialized from localStorage
    expect(result.current.theme).toBe('dark');
  });

  it('should update DOM when theme changes', () => {
    const { result } = renderHook(() => useTheme());
    
    act(() => {
      result.current.setTheme('dark');
    });
    
    expect(document.documentElement.getAttribute('data-theme')).toBe('dark');
  });

  it('should persist theme to localStorage', () => {
    const { result } = renderHook(() => useTheme());
    
    act(() => {
      result.current.setTheme('dark');
    });
    
    const stored = localStorage.getItem('ekumen-theme');
    expect(stored).toBeTruthy();
    
    const parsed = JSON.parse(stored!);
    expect(parsed.state.theme).toBe('dark');
  });
});

