import React, { useEffect } from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Toaster } from 'react-hot-toast'

// Pages
import LandingPage from '@pages/LandingPage'
import Assistant from '@pages/Assistant'
import ChatInterface from '@pages/ChatInterface'
import NewChatInterface from '@pages/NewChatInterface'
import VoiceJournal from '@pages/VoiceJournal'
import Activities from '@pages/Activities'
import Treatments from '@pages/Treatments'
import Parcelles from '@pages/Parcelles'
import FarmManagement from '@pages/FarmManagement'
import Login from '@pages/Login'
import Register from '@pages/Register'

// Components
import Layout from '@components/Layout'
import NewLayout from '@components/Layout/NewLayout'
import ProtectedRoute from '@components/ProtectedRoute'

// Hooks
import { useAuth, AuthProvider } from '@hooks/useAuth'
import { useTheme } from '@hooks/useTheme'

// Styles
import './index.css'

// Create a client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      retry: 1,
    },
  },
})

function AppContent() {
  const { isAuthenticated } = useAuth()

  return (
    <Router>
      <div className="min-h-screen" style={{
        backgroundColor: 'var(--bg-app)',
        color: 'var(--text-primary)',
        transition: 'var(--transition-theme)'
      }}>
          <Routes>
            {/* Public routes */}
            <Route path="/" element={<LandingPage />} />
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            
            {/* Protected routes */}
            <Route
              path="/assistant"
              element={
                <ProtectedRoute>
                  <NewLayout>
                    <NewChatInterface />
                  </NewLayout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/chat"
              element={
                <ProtectedRoute>
                  <NewLayout>
                    <NewChatInterface />
                  </NewLayout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/journal"
              element={
                <ProtectedRoute>
                  <NewLayout>
                    <VoiceJournal />
                  </NewLayout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/activities"
              element={
                <ProtectedRoute>
                  <NewLayout>
                    <Activities />
                  </NewLayout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/treatments"
              element={
                <ProtectedRoute>
                  <NewLayout>
                    <Treatments />
                  </NewLayout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/parcelles"
              element={
                <ProtectedRoute>
                  <NewLayout>
                    <Parcelles />
                  </NewLayout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/farms"
              element={
                <ProtectedRoute>
                  <NewLayout>
                    <FarmManagement />
                  </NewLayout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/settings"
              element={
                <ProtectedRoute>
                  <NewLayout>
                    <div className="p-6">
                      <h1
                        className="text-2xl font-bold mb-4"
                        style={{ color: 'var(--text-primary)' }}
                      >
                        Paramètres
                      </h1>
                      <p style={{ color: 'var(--text-secondary)' }}>Configuration du système</p>
                    </div>
                  </NewLayout>
                </ProtectedRoute>
              }
            />

            {/* Redirect old dashboard route to assistant */}
            <Route path="/dashboard" element={<Navigate to="/assistant" replace />} />

            {/* Catch-all route - redirect to assistant for authenticated users, login for others */}
            <Route path="*" element={<Navigate to="/assistant" replace />} />
          </Routes>
          
          {/* Toast notifications */}
          <Toaster
            position="top-right"
            toastOptions={{
              duration: 4000,
              style: {
                background: '#363636',
                color: '#fff',
              },
              success: {
                style: {
                  background: '#22c55e',
                },
              },
              error: {
                style: {
                  background: '#ef4444',
                },
              },
            }}
          />
        </div>
      </Router>
  )
}

// Theme Provider Component
function ThemeProvider({ children }: { children: React.ReactNode }) {
  const { theme } = useTheme()

  // Apply theme to document root
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
    document.body.style.backgroundColor = 'var(--bg-app)'
    document.body.style.color = 'var(--text-primary)'
  }, [theme])

  return <>{children}</>
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <ThemeProvider>
          <AppContent />
        </ThemeProvider>
      </AuthProvider>
    </QueryClientProvider>
  )
}

export default App
