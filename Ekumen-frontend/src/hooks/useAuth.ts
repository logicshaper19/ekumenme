import React, { useState, useEffect, createContext, useContext, ReactNode } from 'react'

interface User {
  id: string
  email: string
  full_name?: string
  role: 'farmer' | 'advisor' | 'inspector' | 'admin'
  status: 'active' | 'inactive' | 'suspended' | 'pending_verification'
  language_preference: string
  region_code?: string
}

interface AuthContextType {
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
  login: (email: string, password: string) => Promise<void>
  logout: () => void
  register: (userData: RegisterData) => Promise<void>
}

interface RegisterData {
  email: string
  password: string
  full_name: string
  role: 'farmer' | 'advisor' | 'inspector'
  region_code?: string
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    // Check for existing session on mount
    const checkAuth = async () => {
      try {
        const token = localStorage.getItem('auth_token')
        if (token) {
          // TODO: Validate token with backend
          // For now, simulate a user - check if we have stored user data
          const storedUser = localStorage.getItem('user_data')
          if (storedUser) {
            setUser(JSON.parse(storedUser))
          } else {
            // Fallback to default user
            setUser({
              id: '1',
              email: 'farmer@example.com',
              full_name: 'Jean Dupont',
              role: 'farmer',
              status: 'active',
              language_preference: 'fr',
              region_code: '75'
            })
          }
        }
      } catch (error) {
        console.error('Auth check failed:', error)
        localStorage.removeItem('auth_token')
      } finally {
        setIsLoading(false)
      }
    }

    checkAuth()
  }, [])

  const login = async (email: string, password: string) => {
    setIsLoading(true)
    try {
      // TODO: Implement actual API call
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000))
      
      // Extract name from email for demo purposes
      const emailName = email.split('@')[0]
      const displayName = emailName.charAt(0).toUpperCase() + emailName.slice(1)
      
      const mockUser: User = {
        id: '1',
        email,
        full_name: displayName,
        role: 'farmer',
        status: 'active',
        language_preference: 'fr',
        region_code: '75'
      }
      
      setUser(mockUser)
      localStorage.setItem('auth_token', 'mock_token')
      localStorage.setItem('user_data', JSON.stringify(mockUser))
    } catch (error) {
      console.error('Login failed:', error)
      throw error
    } finally {
      setIsLoading(false)
    }
  }

  const logout = () => {
    setUser(null)
    localStorage.removeItem('auth_token')
    localStorage.removeItem('user_data')
  }

  const register = async (userData: RegisterData) => {
    setIsLoading(true)
    try {
      // TODO: Implement actual API call
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000))
      
      const mockUser: User = {
        id: '1',
        email: userData.email,
        full_name: userData.full_name,
        role: userData.role,
        status: 'pending_verification',
        language_preference: 'fr',
        region_code: userData.region_code
      }
      
      setUser(mockUser)
      localStorage.setItem('auth_token', 'mock_token')
    } catch (error) {
      console.error('Registration failed:', error)
      throw error
    } finally {
      setIsLoading(false)
    }
  }

  const value: AuthContextType = {
    user,
    isAuthenticated: !!user,
    isLoading,
    login,
    logout,
    register
  }

  return React.createElement(
    AuthContext.Provider,
    { value },
    children
  )
}