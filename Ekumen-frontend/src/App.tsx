import React from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Toaster } from 'react-hot-toast'

// Pages
import LandingPage from '@pages/LandingPage'
import Assistant from '@pages/Assistant'
import ChatInterface from '@pages/ChatInterface'
import VoiceJournal from '@pages/VoiceJournal'
import Activities from '@pages/Activities'
import Treatments from '@pages/Treatments'
import Parcelles from '@pages/Parcelles'
import FarmManagement from '@pages/FarmManagement'
import Login from '@pages/Login'
import Register from '@pages/Register'

// Components
import Layout from '@components/Layout'
import ProtectedRoute from '@components/ProtectedRoute'

// Hooks
import { useAuth, AuthProvider } from '@hooks/useAuth'

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
      <div className="min-h-screen bg-gray-50">
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
                  <Layout>
                    <ChatInterface />
                  </Layout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/chat"
              element={
                <ProtectedRoute>
                  <Layout>
                    <ChatInterface />
                  </Layout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/journal"
              element={
                <ProtectedRoute>
                  <Layout>
                    <VoiceJournal />
                  </Layout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/activities"
              element={
                <ProtectedRoute>
                  <Layout>
                    <Activities />
                  </Layout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/treatments"
              element={
                <ProtectedRoute>
                  <Layout>
                    <Treatments />
                  </Layout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/parcelles"
              element={
                <ProtectedRoute>
                  <Layout>
                    <Parcelles />
                  </Layout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/farms"
              element={
                <ProtectedRoute>
                  <Layout>
                    <FarmManagement />
                  </Layout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/settings"
              element={
                <ProtectedRoute>
                  <Layout>
                    <div className="p-6">
                      <h1 className="text-2xl font-bold text-gray-900 mb-4">Paramètres</h1>
                      <p className="text-gray-600">Configuration du système</p>
                    </div>
                  </Layout>
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

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <AppContent />
      </AuthProvider>
    </QueryClientProvider>
  )
}

export default App
