import React, { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { Paperclip, Menu, Lightbulb, ArrowRight, Eye, Cloud, Shovel, TrendingUp, DollarSign, Bell, User, LogOut, Home, MessageCircle, Mic, Wheat, BarChart3, Users, FileText, Settings } from 'lucide-react'

// Components
import { Button } from '@components/ui/Button'

// Hooks
import { useAuth } from '@hooks/useAuth'

const Assistant: React.FC = () => {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const [inputValue, setInputValue] = useState('')

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const navigation = [
    {
      name: 'Tableau de bord',
      href: '/dashboard',
      icon: Home,
      description: 'Vue d\'ensemble de votre exploitation'
    },
    {
      name: 'Assistant IA',
      href: '/assistant',
      icon: MessageCircle,
      description: 'Chat avec les agents spécialisés',
      active: true
    },
    {
      name: 'Journal Vocal',
      href: '/journal',
      icon: Mic,
      description: 'Enregistrement d\'interventions'
    },
    {
      name: 'Gestion Exploitation',
      href: '/farms',
      icon: Wheat,
      description: 'Données et parcelles'
    },
    {
      name: 'Analyses',
      href: '/analyses',
      icon: BarChart3,
      description: 'Rapports et statistiques'
    },
    {
      name: 'Équipe',
      href: '/team',
      icon: Users,
      description: 'Gestion des utilisateurs'
    },
    {
      name: 'Documents',
      href: '/documents',
      icon: FileText,
      description: 'Réglementation et guides'
    },
    {
      name: 'Paramètres',
      href: '/settings',
      icon: Settings,
      description: 'Configuration du système'
    }
  ]

  const suggestions = [
    {
      id: 1,
      title: 'Crop Health',
      icon: Eye,
      color: 'text-green-600'
    },
    {
      id: 2,
      title: 'Weather',
      icon: Cloud,
      color: 'text-gray-600'
    },
    {
      id: 3,
      title: 'Soil Analysis',
      icon: Shovel,
      color: 'text-gray-600'
    },
    {
      id: 4,
      title: 'Yield Forecast',
      icon: TrendingUp,
      color: 'text-green-600'
    },
    {
      id: 5,
      title: 'Market Prices',
      icon: DollarSign,
      color: 'text-gray-600'
    }
  ]

  const handleSuggestionClick = (suggestion: string) => {
    setInputValue(suggestion)
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (inputValue.trim()) {
      // Handle chat submission here
      console.log('Chat message:', inputValue)
      setInputValue('')
    }
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
                    item.active
                      ? 'bg-green-50 text-green-700 border-r-2 border-green-500'
                      : 'text-gray-700 hover:bg-gray-50'
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
        <main className="flex-1 bg-white flex flex-col items-center justify-center px-4">
          {/* Chat Interface */}
          <div className="text-center mb-12">
            <div className="flex items-center justify-center mb-6">
              <div className="w-6 h-6 bg-green-600 rounded flex items-center justify-center mr-2">
                <div className="w-3 h-3 bg-white rounded-sm transform rotate-45"></div>
              </div>
              <h1 className="text-2xl font-semibold text-gray-900">ekumen</h1>
            </div>
            <p className="text-base text-gray-700">
              Welcome, {user?.full_name?.split(' ')[0]?.toLowerCase() || 'elisha'}
            </p>
          </div>

      {/* Chat Input */}
      <div className="w-full max-w-4xl mb-12">
        <form onSubmit={handleSubmit} className="relative">
          <div className="flex items-center bg-gray-100 rounded-2xl p-4">
            <input
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              placeholder="Ask anything about your farm or crops..."
              className="flex-1 bg-transparent text-gray-900 placeholder-gray-500 focus:outline-none text-base"
            />
            
            {/* Action Icons */}
            <div className="flex items-center space-x-2 ml-4">
              <button
                type="button"
                className="p-2 text-gray-500 hover:text-gray-700 transition-colors"
                aria-label="Attach file"
              >
                <Paperclip className="h-4 w-4" />
              </button>
              
              <button
                type="button"
                className="p-2 text-gray-500 hover:text-gray-700 transition-colors"
                aria-label="Menu"
              >
                <Menu className="h-4 w-4" />
              </button>
              
              <button
                type="button"
                className="p-2 text-gray-500 hover:text-gray-700 transition-colors"
                aria-label="Suggestions"
              >
                <Lightbulb className="h-4 w-4" />
              </button>
              
              <button
                type="submit"
                className="p-2 bg-green-600 text-white rounded-full hover:bg-green-700 transition-colors ml-2"
                aria-label="Send message"
              >
                <ArrowRight className="h-4 w-4" />
              </button>
            </div>
          </div>
        </form>
      </div>

      {/* Suggestion Buttons */}
      <div className="w-full max-w-4xl">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
          {suggestions.map((suggestion) => {
            const Icon = suggestion.icon
            return (
              <button
                key={suggestion.id}
                onClick={() => handleSuggestionClick(suggestion.title)}
                className="bg-gray-100 rounded-xl p-4 hover:bg-gray-200 transition-colors text-left group"
              >
                <div className="flex flex-col items-center text-center">
                  <div className={`p-2 rounded-lg mb-3`}>
                    <Icon className={`h-5 w-5 ${suggestion.color}`} />
                  </div>
                  <span className="text-sm font-medium text-gray-900">
                    {suggestion.title}
                  </span>
                </div>
              </button>
            )
          })}
        </div>
      </div>
        </main>
      </div>
    </div>
  )
}

export default Assistant
