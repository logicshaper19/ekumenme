import React, { useState } from 'react'
import { NavLink } from 'react-router-dom'
import { Menu, Bell, User, LogOut, Settings, Mic, BarChart3, Beaker, MapPin, ChevronDown } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'

// Components
import { Logo } from '@components/Logo'
import { Button } from '@components/ui/Button'

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
    <header className="bg-white border-b border-gray-200 shadow-sm">
      <div className="flex items-center justify-between px-4 py-3 sm:px-6 lg:px-8">
        {/* Left side */}
        <div className="flex items-center space-x-6">
          {/* Menu button */}
          <button
            onClick={onMenuClick}
            className="p-2 rounded-md text-gray-400 hover:text-gray-500 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-primary-500"
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
                    `flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors ${
                      isActive
                        ? 'bg-primary-50 text-primary-700'
                        : 'text-gray-700 hover:bg-gray-100 hover:text-gray-900'
                    }`
                  }
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
            className="md:hidden p-2 rounded-md text-gray-400 hover:text-gray-500 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-primary-500"
            aria-label="Menu navigation"
          >
            <Menu className="h-5 w-5" />
          </button>

          {/* Notifications */}
          <button
            className="p-2 rounded-md text-gray-400 hover:text-gray-500 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-primary-500"
            aria-label="Notifications"
          >
            <Bell className="h-5 w-5" />
          </button>

          {/* User menu */}
          <div className="relative">
            <button
              onClick={() => setShowUserMenu(!showUserMenu)}
              className="flex items-center space-x-3 p-2 rounded-md hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              <div className="hidden sm:block text-right">
                <p className="text-sm font-medium text-gray-900">
                  {user?.full_name || user?.email}
                </p>
                <p className="text-xs text-gray-500">
                  {user?.role === 'farmer' ? 'Agriculteur' :
                   user?.role === 'advisor' ? 'Conseiller' :
                   user?.role === 'inspector' ? 'Inspecteur' : 'Administrateur'}
                </p>
              </div>

              <div className="flex items-center space-x-1">
                <div className="p-2 bg-gray-100 rounded-full">
                  <User className="h-4 w-4 text-gray-600" />
                </div>
                <ChevronDown className="h-4 w-4 text-gray-400" />
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
                  className="absolute right-0 mt-2 w-56 bg-white rounded-md shadow-lg border border-gray-200 z-50"
                  onMouseLeave={() => setShowUserMenu(false)}
                >
                  <div className="py-1">
                    <NavLink
                      to="/settings"
                      className="flex items-center px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                      onClick={() => setShowUserMenu(false)}
                    >
                      <Settings className="h-4 w-4 mr-3" />
                      Paramètres
                    </NavLink>
                    <div className="border-t border-gray-100"></div>
                    <button
                      onClick={() => {
                        setShowUserMenu(false)
                        handleLogout()
                      }}
                      className="flex items-center w-full px-4 py-2 text-sm text-red-600 hover:bg-red-50"
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
            className="md:hidden border-t border-gray-200 bg-white overflow-hidden"
          >
            <nav className="px-4 py-2 space-y-1">
              {topNavigation.map((item) => {
                const Icon = item.icon
                return (
                  <NavLink
                    key={item.name}
                    to={item.href}
                    className={({ isActive }) =>
                      `flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors ${
                        isActive
                          ? 'bg-primary-50 text-primary-700'
                          : 'text-gray-700 hover:bg-gray-100 hover:text-gray-900'
                      }`
                    }
                    onClick={() => setShowMobileMenu(false)}
                  >
                    <Icon className="h-4 w-4 mr-3" />
                    <div>
                      <div>{item.name}</div>
                      <div className="text-xs text-gray-500">{item.description}</div>
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
