import React, { useState } from 'react'
import { motion } from 'framer-motion'
import { 
  TrendingUp, 
  TrendingDown, 
  MapPin, 
  Calendar,
  Users,
  Search,
  BarChart3,
  PieChart,
  Activity,
  Lightbulb,
  AlertTriangle,
  Target,
  FileText,
  Loader2
} from 'lucide-react'

// Components
import { Button } from '@components/ui/Button'

interface TrendingTopic {
  id: string
  name: string
  volume: number
  growth: number
  color: string
}

interface ProductAnalytic {
  name: string
  queries: number
  growth: number
}

interface ComplianceTheme {
  name: string
  volume: number
  trend: number
}

interface UserBehavior {
  role: string
  percentage: number
  color: string
}

interface QueryJourney {
  from: string
  to: string
  percentage: number
}

const IntelligenceTab: React.FC = () => {
  const [selectedTopic, setSelectedTopic] = useState<TrendingTopic | null>(null)
  const [selectedProduct, setSelectedProduct] = useState<ProductAnalytic | null>(null)
  
  // Content intelligence state
  const [contentInsights, setContentInsights] = useState<any>(null)
  const [insightsLoading, setInsightsLoading] = useState(false)

  // Mock data - will be replaced with real API calls
  const trendingTopics: TrendingTopic[] = [
    { id: '1', name: 'Mélange de cuve', volume: 1247, growth: 89, color: 'bg-red-500' },
    { id: '2', name: 'ZNT calcul', volume: 892, growth: 45, color: 'bg-orange-500' },
    { id: '3', name: 'Conditions météo', volume: 756, growth: 23, color: 'bg-yellow-500' },
    { id: '4', name: 'DAR délai', volume: 634, growth: 12, color: 'bg-green-500' },
    { id: '5', name: 'Dosage précis', volume: 521, growth: -5, color: 'bg-blue-500' },
    { id: '6', name: 'Équipement', volume: 445, growth: -12, color: 'bg-purple-500' }
  ]

  const productAnalytics: ProductAnalytic[] = [
    { name: 'Roundup', queries: 1247, growth: 23 },
    { name: 'Opus', queries: 645, growth: 45 },
    { name: 'Amistar', queries: 456, growth: 12 },
    { name: 'Tilt', queries: 389, growth: -8 },
    { name: 'Fusilade', queries: 298, growth: 34 },
    { name: 'Basta', queries: 234, growth: -15 },
    { name: 'Liberty', queries: 198, growth: 67 },
    { name: 'Touchdown', queries: 156, growth: -23 },
    { name: 'Stomp', queries: 134, growth: 8 },
    { name: 'Sencor', queries: 98, growth: -5 }
  ]

  const complianceThemes: ComplianceTheme[] = [
    { name: 'ZNT', volume: 892, trend: 45 },
    { name: 'Dosage', volume: 634, trend: 12 },
    { name: 'DAR', volume: 445, trend: -8 },
    { name: 'Équipement', volume: 298, trend: 23 },
    { name: 'Formation', volume: 156, trend: -12 }
  ]

  const userBehavior: UserBehavior[] = [
    { role: 'Agriculteurs', percentage: 51, color: 'bg-primary-500' },
    { role: 'Agronomes', percentage: 29, color: 'bg-warning-500' },
    { role: 'Distributeurs', percentage: 20, color: 'bg-info-500' }
  ]

  const queryJourneys: QueryJourney[] = [
    { from: 'Guide Roundup', to: 'Exigences ZNT', percentage: 67 },
    { from: 'Guide Roundup', to: 'Conditions météo', percentage: 45 },
    { from: 'Guide Roundup', to: 'Équipement', percentage: 38 },
    { from: 'Checklist ZNT', to: 'Calculs de distance', percentage: 89 },
    { from: 'Checklist ZNT', to: 'Formation sécurité', percentage: 34 }
  ]

  const getGrowthColor = (growth: number) => {
    if (growth > 20) return 'text-red-600'
    if (growth > 0) return 'text-orange-600'
    if (growth > -10) return 'text-blue-600'
    return 'text-gray-600'
  }

  const getGrowthIcon = (growth: number) => {
    if (growth > 0) return <TrendingUp className="w-4 h-4" />
    return <TrendingDown className="w-4 h-4" />
  }

  // Load content intelligence insights
  const loadContentInsights = async () => {
    setInsightsLoading(true)
    try {
      // Import the service dynamically to avoid circular dependencies
      const { knowledgeBaseService } = await import('@services/knowledgeBaseService')
      const overview = await knowledgeBaseService.getKnowledgeBaseOverview()
      
      // Mock content insights based on the overview data
      const mockInsights = {
        contentGaps: [
          {
            id: '1',
            title: 'Guide météo pour applications',
            description: 'Les utilisateurs recherchent souvent des informations sur les conditions météo optimales',
            priority: 'high',
            impact: 8,
            effort: 6,
            relatedQueries: ['conditions météo Roundup', 'vent application pesticides', 'température optimale'],
            queryCount: 234
          },
          {
            id: '2',
            title: 'Calculs ZNT avancés',
            description: 'Besoin de guides plus détaillés pour les calculs de ZNT complexes',
            priority: 'medium',
            impact: 7,
            effort: 8,
            relatedQueries: ['ZNT cours eau', 'calcul distance ZNT', 'ZNT bâtiments'],
            queryCount: 156
          }
        ],
        performanceInsights: [
          {
            type: 'underperforming',
            title: 'Documents avec faible taux de citation',
            description: '3 documents ont un taux de citation inférieur à 30%',
            documents: ['Guide Équipement', 'Checklist Formation', 'Manuel Sécurité'],
            recommendation: 'Réviser le contenu pour améliorer la pertinence'
          },
          {
            type: 'opportunity',
            title: 'Sujets en forte croissance',
            description: 'Les questions sur le mélange de cuve ont augmenté de 89%',
            opportunity: 'Créer un guide dédié au mélange de cuve',
            potentialImpact: 'Élevé'
          }
        ],
        userBehaviorInsights: [
          {
            insight: 'Les agriculteurs représentent 51% des utilisateurs',
            recommendation: 'Adapter le contenu pour être plus accessible aux agriculteurs'
          },
          {
            insight: 'Pic d\'utilisation au printemps (mars-mai)',
            recommendation: 'Préparer du contenu saisonnier pour le printemps'
          }
        ]
      }
      
      setContentInsights(mockInsights)
    } catch (error) {
      console.error('Error loading content insights:', error)
    } finally {
      setInsightsLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* Trending Topics */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Sujets Tendance</h3>
          <Search className="w-5 h-5 text-gray-400" />
        </div>
        
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
          {trendingTopics.map((topic, index) => (
            <motion.div
              key={topic.id}
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: index * 0.1 }}
              className="relative cursor-pointer group"
              onClick={() => setSelectedTopic(topic)}
            >
              <div className={`${topic.color} rounded-lg p-4 text-white relative overflow-hidden`}>
                <div className="relative z-10">
                  <div className="text-sm font-medium mb-1">{topic.name}</div>
                  <div className="text-xs opacity-90">{topic.volume} requêtes</div>
                  <div className={`text-xs flex items-center mt-1 ${getGrowthColor(topic.growth)}`}>
                    {getGrowthIcon(topic.growth)}
                    <span className="ml-1">{topic.growth > 0 ? '+' : ''}{topic.growth}%</span>
                  </div>
                </div>
                <div className="absolute inset-0 bg-black bg-opacity-10 group-hover:bg-opacity-20 transition-opacity" />
              </div>
            </motion.div>
          ))}
        </div>
      </div>

      {/* Product Analytics */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Analytiques Produits</h3>
          <BarChart3 className="w-5 h-5 text-gray-400" />
        </div>
        
        <div className="space-y-3">
          {productAnalytics.map((product, index) => (
            <motion.div
              key={product.name}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.05 }}
              className="flex items-center justify-between p-3 bg-gray-50 rounded-lg cursor-pointer hover:bg-gray-100 transition-colors"
              onClick={() => setSelectedProduct(product)}
            >
              <div className="flex items-center">
                <div className="w-3 h-3 bg-primary-500 rounded-full mr-3" />
                <span className="font-medium text-gray-900">{product.name}</span>
              </div>
              <div className="flex items-center space-x-4">
                <div className="text-sm text-gray-600">{product.queries} requêtes</div>
                <div className={`text-sm flex items-center ${getGrowthColor(product.growth)}`}>
                  {getGrowthIcon(product.growth)}
                  <span className="ml-1">{product.growth > 0 ? '+' : ''}{product.growth}%</span>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </div>

      {/* Compliance Themes */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Thèmes Réglementaires</h3>
          <Activity className="w-5 h-5 text-gray-400" />
        </div>
        
        <div className="space-y-4">
          {complianceThemes.map((theme, index) => (
            <motion.div
              key={theme.name}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
              className="flex items-center justify-between"
            >
              <div className="flex items-center">
                <div className="w-4 h-4 bg-warning-500 rounded-full mr-3" />
                <span className="font-medium text-gray-900">{theme.name}</span>
              </div>
              <div className="flex items-center space-x-4">
                <div className="text-sm text-gray-600">{theme.volume} requêtes</div>
                <div className={`text-sm flex items-center ${getGrowthColor(theme.trend)}`}>
                  {getGrowthIcon(theme.trend)}
                  <span className="ml-1">{theme.trend > 0 ? '+' : ''}{theme.trend}%</span>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </div>

      {/* User Behavior */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* By Role */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">Par Rôle</h3>
            <Users className="w-5 h-5 text-gray-400" />
          </div>
          
          <div className="space-y-3">
            {userBehavior.map((behavior, index) => (
              <motion.div
                key={behavior.role}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.1 }}
                className="flex items-center justify-between"
              >
                <span className="text-sm font-medium text-gray-900">{behavior.role}</span>
                <div className="flex items-center">
                  <div className="w-20 bg-gray-200 rounded-full h-2 mr-2">
                    <div
                      className={`h-2 rounded-full ${behavior.color}`}
                      style={{ width: `${behavior.percentage}%` }}
                    />
                  </div>
                  <span className="text-sm text-gray-600">{behavior.percentage}%</span>
                </div>
              </motion.div>
            ))}
          </div>
        </div>

        {/* By Region */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">Par Région</h3>
            <MapPin className="w-5 h-5 text-gray-400" />
          </div>
          
          <div className="text-center py-8">
            <div className="w-32 h-32 bg-gray-100 rounded-full mx-auto mb-4 flex items-center justify-center">
              <MapPin className="w-8 h-8 text-gray-400" />
            </div>
            <p className="text-sm text-gray-600">Carte de chaleur régionale</p>
            <p className="text-xs text-gray-500 mt-1">Bretagne: 23% | Nouvelle-Aquitaine: 18%</p>
          </div>
        </div>

        {/* By Season */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">Par Saison</h3>
            <Calendar className="w-5 h-5 text-gray-400" />
          </div>
          
          <div className="text-center py-8">
            <div className="w-32 h-32 bg-gray-100 rounded-full mx-auto mb-4 flex items-center justify-center">
              <Calendar className="w-8 h-8 text-gray-400" />
            </div>
            <p className="text-sm text-gray-600">Calendrier saisonnier</p>
            <p className="text-xs text-gray-500 mt-1">Pic printemps: Mars-Mai</p>
          </div>
        </div>
      </div>

      {/* Query Journeys */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Parcours de Requêtes</h3>
          <PieChart className="w-5 h-5 text-gray-400" />
        </div>
        
        <div className="space-y-4">
          {queryJourneys.map((journey, index) => (
            <motion.div
              key={`${journey.from}-${journey.to}`}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.1 }}
              className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
            >
              <div className="flex items-center">
                <div className="text-sm font-medium text-gray-900">{journey.from}</div>
                <div className="mx-2 text-gray-400">→</div>
                <div className="text-sm text-gray-600">{journey.to}</div>
              </div>
              <div className="flex items-center">
                <div className="w-16 bg-gray-200 rounded-full h-2 mr-2">
                  <div
                    className="h-2 rounded-full bg-primary-500"
                    style={{ width: `${journey.percentage}%` }}
                  />
                </div>
                <span className="text-sm text-gray-600">{journey.percentage}%</span>
              </div>
            </motion.div>
          ))}
        </div>
      </div>

      {/* Content Intelligence Insights */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Intelligence de Contenu</h3>
          <div className="flex items-center space-x-2">
            <Lightbulb className="w-5 h-5 text-gray-400" />
            <Button
              onClick={loadContentInsights}
              disabled={insightsLoading}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              {insightsLoading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Target className="h-4 w-4" />
              )}
              {insightsLoading ? 'Analyse...' : 'Analyser le Contenu'}
            </Button>
          </div>
        </div>
        
        <p className="text-sm text-gray-600 mb-4">
          Analysez les lacunes de contenu, les opportunités d'amélioration et les insights basés sur l'utilisation réelle.
        </p>

        {contentInsights && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-6"
          >
            {/* Content Gaps */}
            <div>
              <h4 className="font-medium text-gray-900 mb-3 flex items-center">
                <AlertTriangle className="h-4 w-4 mr-2 text-orange-500" />
                Lacunes de Contenu Identifiées
              </h4>
              <div className="space-y-3">
                {contentInsights.contentGaps.map((gap: any, index: number) => (
                  <motion.div
                    key={gap.id}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.1 }}
                    className="p-4 bg-orange-50 border border-orange-200 rounded-lg"
                  >
                    <div className="flex items-start justify-between mb-2">
                      <div>
                        <h5 className="font-medium text-orange-900">{gap.title}</h5>
                        <p className="text-sm text-orange-700 mt-1">{gap.description}</p>
                      </div>
                      <div className="text-right">
                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                          gap.priority === 'high' ? 'bg-red-100 text-red-800' :
                          gap.priority === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                          'bg-green-100 text-green-800'
                        }`}>
                          {gap.priority === 'high' ? 'Priorité Haute' :
                           gap.priority === 'medium' ? 'Priorité Moyenne' : 'Priorité Basse'}
                        </span>
                      </div>
                    </div>
                    <div className="flex items-center justify-between text-xs text-orange-600">
                      <span>Impact: {gap.impact}/10 | Effort: {gap.effort}/10</span>
                      <span>{gap.queryCount} requêtes liées</span>
                    </div>
                    <div className="mt-2">
                      <p className="text-xs text-orange-600 font-medium">Requêtes associées:</p>
                      <div className="flex flex-wrap gap-1 mt-1">
                        {gap.relatedQueries.map((query: string, qIndex: number) => (
                          <span key={qIndex} className="text-xs bg-orange-100 text-orange-800 px-2 py-1 rounded">
                            "{query}"
                          </span>
                        ))}
                      </div>
                    </div>
                  </motion.div>
                ))}
              </div>
            </div>

            {/* Performance Insights */}
            <div>
              <h4 className="font-medium text-gray-900 mb-3 flex items-center">
                <BarChart3 className="h-4 w-4 mr-2 text-blue-500" />
                Insights de Performance
              </h4>
              <div className="space-y-3">
                {contentInsights.performanceInsights.map((insight: any, index: number) => (
                  <motion.div
                    key={index}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.1 }}
                    className={`p-4 rounded-lg border ${
                      insight.type === 'underperforming' ? 'bg-red-50 border-red-200' :
                      insight.type === 'opportunity' ? 'bg-green-50 border-green-200' :
                      'bg-blue-50 border-blue-200'
                    }`}
                  >
                    <div className="flex items-start justify-between mb-2">
                      <div>
                        <h5 className={`font-medium ${
                          insight.type === 'underperforming' ? 'text-red-900' :
                          insight.type === 'opportunity' ? 'text-green-900' :
                          'text-blue-900'
                        }`}>
                          {insight.title}
                        </h5>
                        <p className={`text-sm mt-1 ${
                          insight.type === 'underperforming' ? 'text-red-700' :
                          insight.type === 'opportunity' ? 'text-green-700' :
                          'text-blue-700'
                        }`}>
                          {insight.description}
                        </p>
                      </div>
                      <div className={`p-2 rounded-full ${
                        insight.type === 'underperforming' ? 'bg-red-100' :
                        insight.type === 'opportunity' ? 'bg-green-100' :
                        'bg-blue-100'
                      }`}>
                        {insight.type === 'underperforming' ? (
                          <AlertTriangle className="h-4 w-4 text-red-600" />
                        ) : insight.type === 'opportunity' ? (
                          <TrendingUp className="h-4 w-4 text-green-600" />
                        ) : (
                          <Lightbulb className="h-4 w-4 text-blue-600" />
                        )}
                      </div>
                    </div>
                    <div className={`text-sm ${
                      insight.type === 'underperforming' ? 'text-red-600' :
                      insight.type === 'opportunity' ? 'text-green-600' :
                      'text-blue-600'
                    }`}>
                      <strong>Recommandation:</strong> {insight.recommendation || insight.opportunity}
                    </div>
                  </motion.div>
                ))}
              </div>
            </div>

            {/* User Behavior Insights */}
            <div>
              <h4 className="font-medium text-gray-900 mb-3 flex items-center">
                <Users className="h-4 w-4 mr-2 text-purple-500" />
                Insights Comportement Utilisateur
              </h4>
              <div className="space-y-3">
                {contentInsights.userBehaviorInsights.map((insight: any, index: number) => (
                  <motion.div
                    key={index}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.1 }}
                    className="p-4 bg-purple-50 border border-purple-200 rounded-lg"
                  >
                    <div className="flex items-start space-x-3">
                      <div className="p-2 bg-purple-100 rounded-full">
                        <Users className="h-4 w-4 text-purple-600" />
                      </div>
                      <div className="flex-1">
                        <p className="text-sm font-medium text-purple-900 mb-1">
                          {insight.insight}
                        </p>
                        <p className="text-sm text-purple-700">
                          <strong>Action suggérée:</strong> {insight.recommendation}
                        </p>
                      </div>
                    </div>
                  </motion.div>
                ))}
              </div>
            </div>
          </motion.div>
        )}
      </div>

      {/* Topic Detail Modal */}
      {selectedTopic && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4"
          >
            <div className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-900">{selectedTopic.name}</h3>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setSelectedTopic(null)}
                >
                  Fermer
                </Button>
              </div>
              
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="p-4 bg-gray-50 rounded-lg">
                    <div className="text-2xl font-bold text-gray-900">{selectedTopic.volume}</div>
                    <div className="text-sm text-gray-600">Volume de requêtes</div>
                  </div>
                  <div className="p-4 bg-gray-50 rounded-lg">
                    <div className={`text-2xl font-bold ${getGrowthColor(selectedTopic.growth)}`}>
                      {selectedTopic.growth > 0 ? '+' : ''}{selectedTopic.growth}%
                    </div>
                    <div className="text-sm text-gray-600">Taux de croissance</div>
                  </div>
                </div>
                
                <div>
                  <h4 className="font-medium text-gray-900 mb-2">Exemples de questions</h4>
                  <ul className="text-sm text-gray-600 space-y-1">
                    <li>• "Comment calculer la ZNT pour Roundup ?"</li>
                    <li>• "Quelle est la distance minimale pour les cours d'eau ?"</li>
                    <li>• "ZNT obligatoire pour tous les produits ?"</li>
                  </ul>
                </div>
                
                <div>
                  <h4 className="font-medium text-gray-900 mb-2">Couverture actuelle</h4>
                  <div className="text-sm text-gray-600">
                    Vous avez 2 documents couvrant ce sujet avec un taux de citation de 78%.
                  </div>
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      )}

      {/* Product Detail Modal */}
      {selectedProduct && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4"
          >
            <div className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-900">{selectedProduct.name}</h3>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setSelectedProduct(null)}
                >
                  Fermer
                </Button>
              </div>
              
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="p-4 bg-gray-50 rounded-lg">
                    <div className="text-2xl font-bold text-gray-900">{selectedProduct.queries}</div>
                    <div className="text-sm text-gray-600">Requêtes ce mois</div>
                  </div>
                  <div className="p-4 bg-gray-50 rounded-lg">
                    <div className={`text-2xl font-bold ${getGrowthColor(selectedProduct.growth)}`}>
                      {selectedProduct.growth > 0 ? '+' : ''}{selectedProduct.growth}%
                    </div>
                    <div className="text-sm text-gray-600">Évolution</div>
                  </div>
                </div>
                
                <div>
                  <h4 className="font-medium text-gray-900 mb-2">Questions les plus fréquentes</h4>
                  <ul className="text-sm text-gray-600 space-y-1">
                    <li>• "Dosage {selectedProduct.name} pour blé"</li>
                    <li>• "Conditions d'application {selectedProduct.name}"</li>
                    <li>• "Mélange {selectedProduct.name} avec autres produits"</li>
                  </ul>
                </div>
                
                <div>
                  <h4 className="font-medium text-gray-900 mb-2">Performance de vos documents</h4>
                  <div className="text-sm text-gray-600">
                    Votre "Guide {selectedProduct.name}" a un taux de citation de 84% et génère 4200 citations ce mois.
                  </div>
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      )}
    </div>
  )
}

export default IntelligenceTab
