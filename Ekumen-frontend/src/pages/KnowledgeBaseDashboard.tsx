import React, { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  BarChart3, 
  TrendingUp, 
  Target, 
  Download, 
  Share2,
  RefreshCw,
  Clock,
  FileText
} from 'lucide-react'

// Components
import { Button } from '@components/ui/Button'
import PerformanceTab from '@components/Analytics/PerformanceTab'
import IntelligenceTab from '@components/Analytics/IntelligenceTab'
import ActionPlanTab from '@components/Analytics/ActionPlanTab'
import DocumentsTab from '@components/Analytics/DocumentsTab'


interface Tab {
  id: string
  name: string
  icon: React.ComponentType<any>
  description: string
}

const KnowledgeBaseDashboard: React.FC = () => {
  const [activeTab, setActiveTab] = useState('performance')
  const [lastUpdated, setLastUpdated] = useState(new Date())

  const tabs: Tab[] = [
    {
      id: 'performance',
      name: 'Performance',
      icon: BarChart3,
      description: 'Comment mes contenus se portent-ils ?'
    },
    {
      id: 'intelligence',
      name: 'Intelligence',
      icon: TrendingUp,
      description: 'Que se passe-t-il sur le marché ?'
    },
    {
      id: 'action-plan',
      name: 'Plan d\'Action',
      icon: Target,
      description: 'Que dois-je faire ensuite ?'
    },
    {
      id: 'documents',
      name: 'Mes Documents',
      icon: FileText,
      description: 'Gestion de ma base documentaire'
    }
  ]

  const handleRefresh = () => {
    setLastUpdated(new Date())
    // TODO: Trigger data refresh
  }

  const renderTabContent = () => {
    switch (activeTab) {
      case 'performance':
        return <PerformanceTab />
      case 'intelligence':
        return <IntelligenceTab />
      case 'action-plan':
        return <ActionPlanTab />
      case 'documents':
        return <DocumentsTab />
      default:
        return <PerformanceTab />
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">
                Base de Connaissances & Intelligence
              </h1>
              <p className="text-sm text-gray-600 mt-1">
                Gestion documentaire et intelligence de vos contenus agricoles
              </p>
            </div>
            
            <div className="flex items-center space-x-3">
              {/* Last Updated */}
              <div className="flex items-center text-sm text-gray-500">
                <Clock className="w-4 h-4 mr-1" />
                Dernière mise à jour: {lastUpdated.toLocaleTimeString('fr-FR')}
              </div>
              
              {/* Refresh Button */}
              <Button
                variant="outline"
                size="sm"
                onClick={handleRefresh}
                className="flex items-center"
              >
                <RefreshCw className="w-4 h-4 mr-2" />
                Actualiser
              </Button>
              
              {/* Export Button */}
              <Button
                variant="outline"
                size="sm"
                className="flex items-center"
              >
                <Download className="w-4 h-4 mr-2" />
                Exporter
              </Button>
              
              {/* Share Button */}
              <Button
                variant="outline"
                size="sm"
                className="flex items-center"
              >
                <Share2 className="w-4 h-4 mr-2" />
                Partager
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="bg-white border-b border-gray-200">
        <div className="px-6">
          <nav className="flex space-x-8">
            {tabs.map((tab) => {
              const Icon = tab.icon
              const isActive = activeTab === tab.id
              
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`
                    flex items-center py-4 px-1 border-b-2 font-medium text-sm transition-colors
                    ${isActive 
                      ? 'border-primary-500 text-primary-600' 
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    }
                  `}
                >
                  <Icon className="w-5 h-5 mr-2" />
                  {tab.name}
                  <span className="ml-2 text-xs text-gray-400">
                    {tab.description}
                  </span>
                </button>
              )
            })}
          </nav>
        </div>
      </div>

      {/* Tab Content */}
      <div className="flex-1">
        <AnimatePresence mode="wait">
          <motion.div
            key={activeTab}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            transition={{ duration: 0.2 }}
            className="p-6"
          >
            {renderTabContent()}
          </motion.div>
        </AnimatePresence>
      </div>
    </div>
  )
}

export default KnowledgeBaseDashboard
