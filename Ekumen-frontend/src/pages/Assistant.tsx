import React from 'react'
import { useNavigate, Link, useLocation } from 'react-router-dom'
import { Bell, User, LogOut, MessageCircle, Mic, BarChart3, Settings, MapPin, Beaker, Menu } from 'lucide-react'

// Components
import { Button } from '@components/ui/Button'

// Hooks
import { useAuth } from '@hooks/useAuth'

// Pages
import ChatInterface from './ChatInterface'
import VoiceJournal from './VoiceJournal'
import Activities from './Activities'
import Treatments from './Treatments'
import Parcelles from './Parcelles'

const Assistant: React.FC = () => {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  // Determine which content to show based on current route
  const renderMainContent = () => {
    switch (location.pathname) {
      case '/journal':
        return <VoiceJournal />
      case '/activities':
        return <Activities />
      case '/treatments':
        return <Treatments />
      case '/parcelles':
        return <Parcelles />
      case '/assistant':
      default:
        return <ChatInterface />
    }
  }

  const navigation = [
    {
      name: 'Ekumen Assistant',
      href: '/assistant',
      icon: MessageCircle,
      description: 'Chat avec les agents spécialisés'
    },
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
    },
    {
      name: 'Paramètres',
      href: '/settings',
      icon: Settings,
      description: 'Configuration du système'
    }
  ]

  // Check if navigation item is active
  const isActive = (href: string) => {
    return location.pathname === href
  }

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 shadow-sm">
        <div className="flex items-center justify-between px-6 py-3">
          <div className="flex items-center space-x-4">
            <button className="p-2 rounded-md text-gray-400 hover:text-gray-500 hover:bg-gray-100">
              <Menu className="h-5 w-5" />
            </button>
          </div>
          
          <div className="flex items-center space-x-4">
            <button className="p-2 text-gray-400 hover:text-gray-500">
              <Bell className="h-5 w-5" />
            </button>
            <div className="flex items-center space-x-3">
              <div className="text-right">
                <p className="text-sm font-medium text-gray-900">{user?.full_name || 'Jean Dupont'}</p>
                <p className="text-xs text-gray-500">{user?.role === 'farmer' ? 'Agriculteur' : user?.role || 'Utilisateur'}</p>
              </div>
              <div className="p-2 bg-gray-100 rounded-full">
                <User className="h-4 w-4 text-gray-600" />
              </div>
              <button 
                onClick={handleLogout}
                className="flex items-center space-x-1 text-sm text-gray-500 hover:text-gray-700"
              >
                <span>Déconnexion</span>
                <LogOut className="h-4 w-4" />
              </button>
            </div>
          </div>
        </div>
      </header>

      <div className="flex flex-1">
        {/* Sidebar */}
        <aside className="w-64 bg-white border-r border-gray-200 flex flex-col">
          <div className="flex items-center px-6 py-4 border-b border-gray-200">
            <div className="w-8 h-8 bg-green-600 rounded-lg flex items-center justify-center mr-3">
              <div className="w-4 h-4 bg-white rounded-sm transform rotate-45"></div>
            </div>
            <span className="font-semibold text-gray-900">Assistant Agricole IA</span>
          </div>
          
          <nav className="flex-1 px-4 py-6 space-y-2 overflow-y-auto">
            {navigation.map((item) => {
              const Icon = item.icon
              return (
                <Link
                  key={item.name}
                  to={item.href}
                  className={`flex items-center px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                    isActive(item.href)
                      ? 'bg-green-50 text-green-700 border-r-2 border-green-500'
                      : 'text-gray-700 hover:bg-gray-50 hover:text-green-600'
                  }`}
                >
                  <Icon className="h-5 w-5 mr-3" />
                  <div className="flex-1">
                    <div>{item.name}</div>
                    <div className="text-xs text-gray-500 mt-0.5">{item.description}</div>
                  </div>
                </Link>
              )
            })}
          </nav>
        </aside>

        {/* Main Content */}
        <main className="flex-1 bg-white flex flex-col">
          {renderMainContent()}
        </main>
      </div>
    </div>
  )
}

export default Assistant
