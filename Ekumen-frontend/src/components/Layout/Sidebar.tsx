import React from 'react'
import { NavLink } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import {
  MessageCircle,
  Mic,
  Wheat,
  Settings,
  X,
  BarChart3,
  Users,
  FileText
} from 'lucide-react'

// Components

interface SidebarProps {
  isOpen: boolean
  onClose: () => void
  user?: any
}

const Sidebar: React.FC<SidebarProps> = ({ isOpen, onClose, user }) => {
  const navigation = [
    {
      name: 'Assistant IA',
      href: '/assistant',
      icon: MessageCircle,
      description: 'Chat avec les agents spécialisés'
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
      href: '/analytics',
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

  return (
    <>
      {/* Mobile overlay */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-40 lg:hidden"
            onClick={onClose}
          >
            <div className="absolute inset-0 bg-gray-600 bg-opacity-75" />
          </motion.div>
        )}
      </AnimatePresence>

      {/* Sidebar */}
      <AnimatePresence>
        <motion.div
          initial={false}
          animate={{ x: isOpen ? 0 : '-100%' }}
          transition={{ type: 'tween', duration: 0.3 }}
          className={`
            fixed inset-y-0 left-0 z-50 w-64 bg-white border-r border-gray-200 transform transition-transform duration-300 ease-in-out
            lg:translate-x-0 lg:static lg:inset-0
            ${isOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
          `}
        >
          <div className="flex flex-col h-full">
            {/* Header */}
            <div className="flex items-center justify-end px-6 py-4 border-b border-gray-200">
              <button
                onClick={onClose}
                className="lg:hidden p-2 rounded-md text-gray-400 hover:text-gray-500 hover:bg-gray-100"
                aria-label="Fermer le menu"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {/* Navigation */}
            <nav className="flex-1 px-4 py-6 space-y-2 overflow-y-auto">
              {navigation.map((item) => {
                const Icon = item.icon
                return (
                  <NavLink
                    key={item.name}
                    to={item.href}
                    className={({ isActive }) =>
                      `group flex items-center px-3 py-2 text-sm font-medium rounded-lg transition-colors duration-200 ${
                        isActive
                          ? 'bg-primary-100 text-primary-700 border-r-2 border-primary-500'
                          : 'text-gray-700 hover:bg-gray-100 hover:text-gray-900'
                      }`
                    }
                    onClick={() => {
                      // Close mobile menu when navigating
                      if (window.innerWidth < 1024) {
                        onClose()
                      }
                    }}
                  >
                    <Icon className="mr-3 h-5 w-5 flex-shrink-0" />
                    <div className="flex-1">
                      <div className="font-medium">{item.name}</div>
                      <div className="text-xs text-gray-500 mt-0.5">
                        {item.description}
                      </div>
                    </div>
                  </NavLink>
                )
              })}
            </nav>

            {/* Footer */}
            <div className="px-4 py-4 border-t border-gray-200">
              <div className="text-xs text-gray-500 text-center">
                <p>Assistant Agricole IA v1.0.0</p>
                <p className="mt-1">© 2024 Tous droits réservés</p>
              </div>
            </div>
          </div>
        </motion.div>
      </AnimatePresence>
    </>
  )
}

export default Sidebar
