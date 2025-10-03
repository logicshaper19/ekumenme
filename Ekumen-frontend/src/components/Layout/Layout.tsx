import React, { useState } from 'react'
import { Outlet } from 'react-router-dom'

// Components
import Header from './Header'
import Sidebar from './Sidebar'
import { Logo } from '@components/Logo'

// Hooks
import { useAuth } from '@hooks/useAuth'

interface LayoutProps {
  children?: React.ReactNode
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const [sidebarOpen, setSidebarOpen] = useState(true) // Open by default
  const { user } = useAuth()

  return (
    <div
      className="min-h-screen flex flex-col"
      style={{
        backgroundColor: 'var(--bg-app)',
        color: 'var(--text-primary)',
        transition: 'var(--transition-theme)'
      }}
    >
      {/* Header */}
      <Header
        onMenuClick={() => setSidebarOpen(!sidebarOpen)}
        user={user}
      />

      <div className="flex flex-1">
        {/* Sidebar */}
        <Sidebar
          isOpen={sidebarOpen}
          onClose={() => setSidebarOpen(false)}
          user={user}
        />

        {/* Main content */}
        <main
          className={`flex-1 transition-all duration-300 ${sidebarOpen ? 'ml-10' : 'ml-0'}`}
          style={{
            backgroundColor: 'var(--bg-app)',
            color: 'var(--text-primary)'
          }}
        >
          <div className="px-6 py-1">
            {children || <Outlet />}
          </div>
        </main>
      </div>
    </div>
  )
}

export default Layout
