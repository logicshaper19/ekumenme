import React from 'react'
import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { 
  MessageCircle, 
  Mic, 
  Wheat, 
  Shield, 
  Cloud, 
  Leaf,
  ArrowRight,
  CheckCircle,
  Users,
  BarChart3
} from 'lucide-react'

// Components
import { Logo } from '@components/Logo'
import { Button } from '@components/ui/Button'
import { AgriculturalCard } from '@components/AgriculturalCard'

const LandingPage: React.FC = () => {
  const agents = [
    {
      name: 'Gestionnaire de Données d\'Exploitation',
      icon: Wheat,
      description: 'Analyse des parcelles, rotations culturales et historique des interventions',
      color: 'primary'
    },
    {
      name: 'Conseiller Réglementaire',
      icon: Shield,
      description: 'Conformité AMM, réglementation phytosanitaire et sécurité',
      color: 'warning'
    },
    {
      name: 'Intelligence Météorologique',
      icon: Cloud,
      description: 'Prévisions météo, conditions optimales et alertes climatiques',
      color: 'info'
    },
    {
      name: 'Moniteur de Santé des Cultures',
      icon: Leaf,
      description: 'Détection de maladies, diagnostic et recommandations de traitement',
      color: 'success'
    }
  ]

  const features = [
    {
      title: 'Interface Vocale Intelligente',
      description: 'Enregistrez vos interventions directement sur le terrain avec validation en temps réel',
      icon: Mic
    },
    {
      title: '6 Agents Spécialisés',
      description: 'Des experts IA dédiés à chaque aspect de votre exploitation agricole',
      icon: Users
    },
    {
      title: 'Conformité Réglementaire',
      description: 'Respect automatique des réglementations françaises et européennes',
      icon: Shield
    },
    {
      title: 'Analyses Prédictives',
      description: 'Optimisez vos rendements avec des insights basés sur vos données',
      icon: BarChart3
    }
  ]

  return (
    <div className="min-h-screen bg-white">
      {/* Header */}
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <Logo 
              size="lg"
              showText={true}
              text="Assistant Agricole IA"
            />
            <div className="flex items-center space-x-4">
              <Link to="/login">
                <Button variant="ghost">Connexion</Button>
              </Link>
              <Link to="/register">
                <Button>Commencer</Button>
              </Link>
            </div>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="relative bg-gradient-to-br from-primary-50 to-success-50 py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <motion.h1
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6 }}
              className="text-4xl md:text-6xl font-bold text-gray-900 mb-6"
            >
              Votre Assistant Agricole
              <span className="text-primary-600 block">Intelligent</span>
            </motion.h1>
            
            <motion.p
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.2 }}
              className="text-xl text-gray-600 mb-8 max-w-3xl mx-auto"
            >
              Optimisez votre exploitation avec l'IA. Enregistrez vos interventions par la voix, 
              obtenez des conseils réglementaires en temps réel et maximisez vos rendements.
            </motion.p>
            
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.4 }}
              className="flex flex-col sm:flex-row gap-4 justify-center"
            >
              <Link to="/register">
                <Button size="lg" className="w-full sm:w-auto">
                  Essayer Gratuitement
                  <ArrowRight className="ml-2 h-5 w-5" />
                </Button>
              </Link>
              <Link to="/demo">
                <Button variant="outline" size="lg" className="w-full sm:w-auto">
                  Voir la Démo
                </Button>
              </Link>
            </motion.div>
          </div>
        </div>
      </section>

      {/* Agents Section */}
      <section className="py-20 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
              6 Agents Spécialisés à Votre Service
            </h2>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto">
              Chaque agent est un expert dans son domaine, formé spécifiquement 
              pour l'agriculture française et la réglementation européenne.
            </p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {agents.map((agent, index) => {
              const Icon = agent.icon
              return (
                <motion.div
                  key={agent.name}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.6, delay: index * 0.1 }}
                >
                  <AgriculturalCard
                    type="farm-data"
                    status="info"
                    title={agent.name}
                    icon={<Icon className="h-6 w-6" />}
                    className="h-full"
                  >
                    <p className="text-gray-600 text-sm">
                      {agent.description}
                    </p>
                  </AgriculturalCard>
                </motion.div>
              )
            })}
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
              Fonctionnalités Innovantes
            </h2>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto">
              Une plateforme complète conçue spécifiquement pour les agriculteurs français.
            </p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {features.map((feature, index) => {
              const Icon = feature.icon
              return (
                <motion.div
                  key={feature.title}
                  initial={{ opacity: 0, x: index % 2 === 0 ? -20 : 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.6, delay: index * 0.1 }}
                  className="flex items-start space-x-4 p-6 bg-white rounded-xl shadow-card"
                >
                  <div className="flex-shrink-0">
                    <div className="w-12 h-12 bg-primary-100 rounded-lg flex items-center justify-center">
                      <Icon className="h-6 w-6 text-primary-600" />
                    </div>
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-2">
                      {feature.title}
                    </h3>
                    <p className="text-gray-600">
                      {feature.description}
                    </p>
                  </div>
                </motion.div>
              )
            })}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 bg-primary-600">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <motion.h2
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="text-3xl md:text-4xl font-bold text-white mb-4"
          >
            Prêt à Révolutionner Votre Agriculture ?
          </motion.h2>
          
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="text-xl text-primary-100 mb-8 max-w-3xl mx-auto"
          >
            Rejoignez des centaines d'agriculteurs qui utilisent déjà notre assistant IA 
            pour optimiser leurs exploitations.
          </motion.p>
          
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.4 }}
          >
            <Link to="/register">
              <Button size="lg" variant="secondary" className="bg-white text-primary-600 hover:bg-gray-100">
                Commencer Maintenant
                <ArrowRight className="ml-2 h-5 w-5" />
              </Button>
            </Link>
          </motion.div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-900 text-white py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col md:flex-row justify-between items-center">
            <Logo 
              size="md"
              showText={true}
              text="Assistant Agricole IA"
              className="text-white"
            />
            <div className="mt-4 md:mt-0 text-center md:text-right">
              <p className="text-gray-400">
                © 2024 Assistant Agricole IA. Tous droits réservés.
              </p>
              <p className="text-gray-500 text-sm mt-1">
                Conçu pour les agriculteurs français
              </p>
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}

export default LandingPage
