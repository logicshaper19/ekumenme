import React, { useState } from 'react'
import { NavLink } from 'react-router-dom'
import { Menu, Bell, User, LogOut, Settings, Mic, BarChart3, Beaker, MapPin, ChevronDown } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'

// Components
import { Logo } from '@components/Logo'
import { Button } from '@components/ui/Button'
import { ThemeToggle } from '@components/ThemeToggle'

// Hooks
import { useAuth } from '@hooks/useAuth'

interface HeaderProps {
  onMenuClick: () => void
  user?: any
}

const Header: React.FC<HeaderProps> = ({ onMenuClick, user }) => {
  const { logout } = useAuth()
  const [showUserMenu, setShowUserMenu] = useState(false)
  const [showMobileMenu, setShowMobileMenu] = useState(false)

  const handleLogout = () => {
    logout()
  }

  // Top navigation items
  const topNavigation = [
    {
      name: 'Journal',
      href: '/journal',
      icon: Mic,
      description: 'Enregistrement d\'interventions'
    },
    {
      name: 'Activités',
      href: '/activities',
      icon: BarChart3,
      description: 'Historique des activités agricoles'
    },
    {
      name: 'Traitements',
      href: '/treatments',
      icon: Beaker,
      description: 'Produits phytosanitaires utilisés'
    },
    {
      name: 'Parcelles',
      href: '/parcelles',
      icon: MapPin,
      description: 'Gestion des parcelles'
    }
  ]

  return (
    <>
    <header className="bg-card border-b border-subtle shadow-card">
      <div className="flex items-center justify-between px-4 py-3 sm:px-6 lg:px-8">
        {/* Left side */}
        <div className="flex items-center space-x-6">
          {/* Menu button */}
          <button
            onClick={onMenuClick}
            className="p-2 rounded-md hover:bg-card-hover focus:outline-none focus:ring-2"
            style={{
              color: 'var(--text-muted)',
              '--tw-ring-color': 'var(--brand-500)'
            } as React.CSSProperties}
            aria-label="Ouvrir le menu"
          >
            <Menu className="h-6 w-6" />
          </button>

          {/* Logo */}
          <Logo
            size="md"
            showText={true}
            text="Ekumen"
            clickable={true}
            onClick={() => window.location.href = '/assistant'}
          />

          {/* Top Navigation - Hidden on mobile */}
          <nav className="hidden md:flex items-center space-x-1">
            {topNavigation.map((item) => {
              const Icon = item.icon
              return (
                <NavLink
                  key={item.name}
                  to={item.href}
                  className={({ isActive }) =>
                    `flex items-center px-3 py-2 text-sm font-medium rounded-md transition-theme ${
                      isActive
                        ? ''
                        : ''
                    }`
                  }
                  style={({ isActive }) => ({
                    backgroundColor: isActive ? 'var(--success-bg)' : 'transparent',
                    color: isActive ? 'var(--success-text)' : 'var(--text-primary)'
                  })}
                  onMouseEnter={(e) => {
                    if (!e.currentTarget.classList.contains('active')) {
                      e.currentTarget.style.backgroundColor = 'var(--bg-card-hover)';
                    }
                  }}
                  onMouseLeave={(e) => {
                    if (!e.currentTarget.classList.contains('active')) {
                      e.currentTarget.style.backgroundColor = 'transparent';
                    }
                  }}
                  title={item.description}
                >
                  <Icon className="h-4 w-4 mr-2" />
                  {item.name}
                </NavLink>
              )
            })}
          </nav>
        </div>

        {/* Right side */}
        <div className="flex items-center space-x-2 sm:space-x-4">
          {/* Mobile menu toggle - visible only on mobile */}
          <button
            onClick={() => setShowMobileMenu(!showMobileMenu)}
            className="md:hidden p-2 rounded-md hover:bg-card-hover focus:outline-none focus:ring-2"
            style={{
              color: 'var(--text-muted)',
              '--tw-ring-color': 'var(--brand-500)'
            } as React.CSSProperties}
            aria-label="Menu navigation"
          >
            <Menu className="h-5 w-5" />
          </button>

          {/* Theme Toggle */}
          <ThemeToggle />

          {/* Notifications */}
          <button
            className="p-2 rounded-md hover:bg-card-hover focus:outline-none focus:ring-2"
            style={{
              color: 'var(--text-muted)',
              '--tw-ring-color': 'var(--brand-500)'
            } as React.CSSProperties}
            aria-label="Notifications"
          >
            <Bell className="h-5 w-5" />
          </button>

          {/* User menu */}
          <div className="relative">
            <button
              onClick={() => setShowUserMenu(!showUserMenu)}
              className="flex items-center space-x-3 p-2 rounded-md hover:bg-card-hover focus:outline-none focus:ring-2"
              style={{ '--tw-ring-color': 'var(--brand-500)' } as React.CSSProperties}
            >
              <div className="hidden sm:block text-right">
                <p className="text-sm font-medium text-primary">
                  {user?.full_name || user?.email}
                </p>
                <p className="text-xs text-muted">
                  {user?.role === 'farmer' ? 'Agriculteur' :
                   user?.role === 'advisor' ? 'Conseiller' :
                   user?.role === 'inspector' ? 'Inspecteur' : 'Administrateur'}
                </p>
              </div>

              <div className="flex items-center space-x-1">
                <div className="p-2 rounded-full" style={{ backgroundColor: 'var(--bg-input)' }}>
                  <User className="h-4 w-4" style={{ color: 'var(--text-secondary)' }} />
                </div>
                <ChevronDown className="h-4 w-4" style={{ color: 'var(--text-muted)' }} />
              </div>
            </button>

            {/* Dropdown menu */}
            <AnimatePresence>
              {showUserMenu && (
                <motion.div
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  transition={{ duration: 0.2 }}
                  className="absolute right-0 mt-2 w-56 bg-elevated rounded-md border border-subtle z-50"
                  style={{ boxShadow: 'var(--shadow-lg)' }}
                  onMouseLeave={() => setShowUserMenu(false)}
                >
                  <div className="py-1">
                    <NavLink
                      to="/settings"
                      className="flex items-center px-4 py-2 text-sm text-primary hover:bg-card-hover"
                      onClick={() => setShowUserMenu(false)}
                    >
                      <Settings className="h-4 w-4 mr-3" />
                      Paramètres
                    </NavLink>
                    <div className="border-t" style={{ borderColor: 'var(--border-subtle)' }}></div>
                    <button
                      onClick={() => {
                        setShowUserMenu(false)
                        handleLogout()
                      }}
                      className="flex items-center w-full px-4 py-2 text-sm"
                      style={{
                        color: 'var(--error-600)',
                        ':hover': { backgroundColor: 'var(--error-bg)' }
                      }}
                      onMouseEnter={(e) => e.currentTarget.style.backgroundColor = 'var(--error-bg)'}
                      onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
                    >
                      <LogOut className="h-4 w-4 mr-3" />
                      Déconnexion
                    </button>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>
      </div>

      {/* Mobile Navigation Menu */}
      <AnimatePresence>
        {showMobileMenu && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="md:hidden border-t bg-card overflow-hidden"
            style={{ borderColor: 'var(--border-subtle)' }}
          >
            <nav className="px-4 py-2 space-y-1">
              {topNavigation.map((item) => {
                const Icon = item.icon
                return (
                  <NavLink
                    key={item.name}
                    to={item.href}
                    className="flex items-center px-3 py-2 text-sm font-medium rounded-md transition-theme"
                    style={({ isActive }) => ({
                      backgroundColor: isActive ? 'var(--success-bg)' : 'transparent',
                      color: isActive ? 'var(--success-text)' : 'var(--text-primary)'
                    })}
                    onMouseEnter={(e) => {
                      if (!e.currentTarget.classList.contains('active')) {
                        e.currentTarget.style.backgroundColor = 'var(--bg-card-hover)';
                      }
                    }}
                    onMouseLeave={(e) => {
                      if (!e.currentTarget.classList.contains('active')) {
                        e.currentTarget.style.backgroundColor = 'transparent';
                      }
                    }}
                    onClick={() => setShowMobileMenu(false)}
                  >
                    <Icon className="h-4 w-4 mr-3" />
                    <div>
                      <div>{item.name}</div>
                      <div className="text-xs text-muted">{item.description}</div>
                    </div>
                  </NavLink>
                )
              })}
            </nav>
          </motion.div>
        )}
      </AnimatePresence>
    </header>
    </>
  )
}

export default Header
