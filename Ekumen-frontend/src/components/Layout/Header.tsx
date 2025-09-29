import React from 'react'
import { Menu, Bell, User, LogOut } from 'lucide-react'
import { motion } from 'framer-motion'

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

  const handleLogout = () => {
    logout()
  }

  return (
    <header className="bg-white border-b border-gray-200 shadow-sm">
      <div className="flex items-center justify-between px-4 py-3 sm:px-6 lg:px-8">
        {/* Left side */}
        <div className="flex items-center space-x-4">
          {/* Menu button - always visible */}
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
            text="Assistant Agricole IA"
            clickable={true}
            onClick={() => window.location.href = '/assistant'}
          />
        </div>
        
        {/* Right side */}
        <div className="flex items-center space-x-4">
          {/* Notifications */}
          <button
            className="p-2 rounded-md text-gray-400 hover:text-gray-500 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-primary-500"
            aria-label="Notifications"
          >
            <Bell className="h-6 w-6" />
          </button>
          
          {/* User menu */}
          <div className="flex items-center space-x-3">
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
            
            <div className="flex items-center space-x-2">
              <button
                className="p-2 rounded-md text-gray-400 hover:text-gray-500 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-primary-500"
                aria-label="Profil utilisateur"
              >
                <User className="h-6 w-6" />
              </button>
              
              <Button
                variant="ghost"
                size="sm"
                onClick={handleLogout}
                className="text-gray-500 hover:text-gray-700"
              >
                <LogOut className="h-4 w-4 mr-2" />
                Déconnexion
              </Button>
            </div>
          </div>
        </div>
      </div>
    </header>
  )
}

export default Header
