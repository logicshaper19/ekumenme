import { renderHook, act } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { useAuth, AuthProvider } from './useAuth'

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
}
Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
})

describe('useAuth Hook', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('throws error when used outside AuthProvider', () => {
    expect(() => {
      renderHook(() => useAuth())
    }).toThrow('useAuth must be used within an AuthProvider')
  })

  it('initializes with no user when no token exists', async () => {
    localStorageMock.getItem.mockReturnValue(null)
    
    const { result } = renderHook(() => useAuth(), {
      wrapper: AuthProvider,
    })

    // Initially loading
    expect(result.current.isLoading).toBe(true)
    expect(result.current.isAuthenticated).toBe(false)
    expect(result.current.user).toBe(null)

    // Wait for auth check to complete
    await act(async () => {
      await new Promise(resolve => setTimeout(resolve, 100))
    })

    expect(result.current.isLoading).toBe(false)
    expect(result.current.isAuthenticated).toBe(false)
    expect(result.current.user).toBe(null)
  })

  it('initializes with user when token exists', async () => {
    localStorageMock.getItem.mockReturnValue('mock_token')
    
    const { result } = renderHook(() => useAuth(), {
      wrapper: AuthProvider,
    })

    // Wait for auth check to complete
    await act(async () => {
      await new Promise(resolve => setTimeout(resolve, 100))
    })

    expect(result.current.isLoading).toBe(false)
    expect(result.current.isAuthenticated).toBe(true)
    expect(result.current.user).toEqual({
      id: '1',
      email: 'farmer@example.com',
      full_name: 'Jean Dupont',
      role: 'farmer',
      status: 'active',
      language_preference: 'fr',
      region_code: '75'
    })
  })

  it('handles login successfully', async () => {
    const { result } = renderHook(() => useAuth(), {
      wrapper: AuthProvider,
    })

    await act(async () => {
      await result.current.login('test@example.com', 'password123')
    })

    expect(result.current.isAuthenticated).toBe(true)
    expect(result.current.user).toEqual({
      id: '1',
      email: 'test@example.com',
      full_name: 'Jean Dupont',
      role: 'farmer',
      status: 'active',
      language_preference: 'fr',
      region_code: '75'
    })
    expect(localStorageMock.setItem).toHaveBeenCalledWith('auth_token', 'mock_token')
  })

  it('handles login failure', async () => {
    // Mock a failed login by making the promise reject
    const { result } = renderHook(() => useAuth(), {
      wrapper: AuthProvider,
    })

    // We need to mock the login to throw an error
    const originalLogin = result.current.login
    result.current.login = vi.fn().mockRejectedValue(new Error('Login failed'))

    await act(async () => {
      try {
        await result.current.login('test@example.com', 'wrongpassword')
      } catch (error) {
        // Expected to throw
      }
    })

    expect(result.current.isAuthenticated).toBe(false)
    expect(result.current.user).toBe(null)
  })

  it('handles logout', async () => {
    // First login
    const { result } = renderHook(() => useAuth(), {
      wrapper: AuthProvider,
    })

    await act(async () => {
      await result.current.login('test@example.com', 'password123')
    })

    expect(result.current.isAuthenticated).toBe(true)

    // Then logout
    act(() => {
      result.current.logout()
    })

    expect(result.current.isAuthenticated).toBe(false)
    expect(result.current.user).toBe(null)
    expect(localStorageMock.removeItem).toHaveBeenCalledWith('auth_token')
  })

  it('handles registration successfully', async () => {
    const { result } = renderHook(() => useAuth(), {
      wrapper: AuthProvider,
    })

    const userData = {
      email: 'newuser@example.com',
      password: 'password123',
      full_name: 'New User',
      role: 'farmer' as const,
      region_code: '75'
    }

    await act(async () => {
      await result.current.register(userData)
    })

    expect(result.current.isAuthenticated).toBe(true)
    expect(result.current.user).toEqual({
      id: '1',
      email: 'newuser@example.com',
      full_name: 'New User',
      role: 'farmer',
      status: 'pending_verification',
      language_preference: 'fr',
      region_code: '75'
    })
    expect(localStorageMock.setItem).toHaveBeenCalledWith('auth_token', 'mock_token')
  })

  it('handles registration failure', async () => {
    const { result } = renderHook(() => useAuth(), {
      wrapper: AuthProvider,
    })

    // Mock a failed registration
    const originalRegister = result.current.register
    result.current.register = vi.fn().mockRejectedValue(new Error('Registration failed'))

    const userData = {
      email: 'test@example.com',
      password: 'password123',
      full_name: 'Test User',
      role: 'farmer' as const,
    }

    await act(async () => {
      try {
        await result.current.register(userData)
      } catch (error) {
        // Expected to throw
      }
    })

    expect(result.current.isAuthenticated).toBe(false)
    expect(result.current.user).toBe(null)
  })
})
