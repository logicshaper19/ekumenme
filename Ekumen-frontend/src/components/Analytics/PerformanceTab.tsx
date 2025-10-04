import React, { useState } from 'react'
import { motion } from 'framer-motion'
import { 
  TrendingUp, 
  TrendingDown, 
  Eye, 
  ThumbsUp,
  AlertTriangle,
  CheckCircle,
  Clock,
  FileText,
  Filter,
  Target,
  BarChart3,
  Loader2,
  Zap
} from 'lucide-react'

// Components
import { Button } from '@components/ui/Button'

interface Document {
  id: string
  name: string
  audience: 'public' | 'internal' | 'customers'
  retrievals: number
  citations: number
  citationRate: number
  satisfaction: number
  trend: number
  userInteractions: number
  status: 'good' | 'warning' | 'critical'
}

interface PortfolioOverview {
  totalDocuments: number
  totalQueries: number
  averageSatisfaction: number
  documentsNeedingAttention: number
}

const PerformanceTab: React.FC = () => {
  const [selectedDocument, setSelectedDocument] = useState<Document | null>(null)
  const [sortBy, setSortBy] = useState<'performance' | 'usage' | 'trend'>('performance')
  const [filterAudience, setFilterAudience] = useState<'all' | 'public' | 'internal' | 'customers'>('all')
  const [showOnlyAlerts, setShowOnlyAlerts] = useState(false)
  
  // Source attribution analytics state
  const [sourceAttributionQuery, setSourceAttributionQuery] = useState('')
  const [sourceAttribution, setSourceAttribution] = useState<any>(null)
  const [attributionLoading, setAttributionLoading] = useState(false)

  // Mock data - will be replaced with real API calls
  const portfolioOverview: PortfolioOverview = {
    totalDocuments: 23,
    totalQueries: 12450,
    averageSatisfaction: 88,
    documentsNeedingAttention: 2
  }

  const documents: Document[] = [
    {
      id: '1',
      name: 'Guide d\'Application Roundup',
      audience: 'public',
      retrievals: 5000,
      citations: 4200,
      citationRate: 84,
      satisfaction: 92,
      trend: 23,
      userInteractions: 950,
      status: 'good'
    },
    {
      id: '2',
      name: 'Checklist ZNT',
      audience: 'internal',
      retrievals: 890,
      citations: 107,
      citationRate: 12,
      satisfaction: 0,
      trend: -15,
      userInteractions: 45,
      status: 'critical'
    },
    {
      id: '3',
      name: 'Guide de Mélange de Produits',
      audience: 'customers',
      retrievals: 2100,
      citations: 1260,
      citationRate: 60,
      satisfaction: 85,
      trend: -5,
      userInteractions: 320,
      status: 'warning'
    }
  ]

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'good': return 'text-success-600 bg-success-50'
      case 'warning': return 'text-warning-600 bg-warning-50'
      case 'critical': return 'text-error-600 bg-error-50'
      default: return 'text-gray-600 bg-gray-50'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'good': return <CheckCircle className="w-4 h-4" />
      case 'warning': return <Clock className="w-4 h-4" />
      case 'critical': return <AlertTriangle className="w-4 h-4" />
      default: return null
    }
  }

  const filteredDocuments = documents.filter(doc => {
    if (filterAudience !== 'all' && doc.audience !== filterAudience) return false
    if (showOnlyAlerts && doc.status === 'good') return false
    return true
  })

  const sortedDocuments = [...filteredDocuments].sort((a, b) => {
    switch (sortBy) {
      case 'performance':
        return a.citationRate - b.citationRate // Worst first
      case 'usage':
        return b.retrievals - a.retrievals // Highest first
      case 'trend':
        return a.trend - b.trend // Declining first
      default:
        return 0
    }
  })

  // Handle source attribution query
  const handleSourceAttribution = async () => {
    if (!sourceAttributionQuery.trim() || !selectedDocument) return
    
    setAttributionLoading(true)
    try {
      // Import the service dynamically to avoid circular dependencies
      const { knowledgeBaseService } = await import('@services/knowledgeBaseService')
      const result = await knowledgeBaseService.getSourceAttribution(sourceAttributionQuery)
      setSourceAttribution(result)
    } catch (error) {
      console.error('Error getting source attribution:', error)
    } finally {
      setAttributionLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* Portfolio Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white p-6 rounded-lg shadow-sm border border-gray-200"
        >
          <div className="flex items-center">
            <FileText className="w-8 h-8 text-primary-600" />
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Documents totaux</p>
              <p className="text-2xl font-bold text-gray-900">{portfolioOverview.totalDocuments}</p>
            </div>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="bg-white p-6 rounded-lg shadow-sm border border-gray-200"
        >
          <div className="flex items-center">
            <Eye className="w-8 h-8 text-info-600" />
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Requêtes ce mois</p>
              <p className="text-2xl font-bold text-gray-900">{portfolioOverview.totalQueries.toLocaleString()}</p>
            </div>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="bg-white p-6 rounded-lg shadow-sm border border-gray-200"
        >
          <div className="flex items-center">
            <ThumbsUp className="w-8 h-8 text-success-600" />
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Satisfaction moyenne</p>
              <p className="text-2xl font-bold text-gray-900">{portfolioOverview.averageSatisfaction}%</p>
            </div>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="bg-white p-6 rounded-lg shadow-sm border border-gray-200"
        >
          <div className="flex items-center">
            <AlertTriangle className="w-8 h-8 text-error-600" />
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Attention requise</p>
              <p className="text-2xl font-bold text-gray-900">{portfolioOverview.documentsNeedingAttention}</p>
            </div>
          </div>
        </motion.div>
      </div>

      {/* Filters and Controls */}
      <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200">
        <div className="flex flex-wrap items-center gap-4">
          <div className="flex items-center space-x-2">
            <Filter className="w-4 h-4 text-gray-500" />
            <span className="text-sm font-medium text-gray-700">Filtres:</span>
          </div>
          
          <div className="flex items-center space-x-2">
            <input
              type="checkbox"
              id="alerts-only"
              checked={showOnlyAlerts}
              onChange={(e) => setShowOnlyAlerts(e.target.checked)}
              className="rounded border-gray-300"
            />
            <label htmlFor="alerts-only" className="text-sm text-gray-700">
              Afficher seulement les alertes
            </label>
          </div>

          <select
            value={filterAudience}
            onChange={(e) => setFilterAudience(e.target.value as any)}
            className="px-3 py-1 border border-gray-300 rounded-md text-sm"
          >
            <option value="all">Tous les publics</option>
            <option value="public">Public</option>
            <option value="internal">Interne</option>
            <option value="customers">Clients</option>
          </select>

          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as any)}
            className="px-3 py-1 border border-gray-300 rounded-md text-sm"
          >
            <option value="performance">Performance (pire en premier)</option>
            <option value="usage">Utilisation (plus élevé en premier)</option>
            <option value="trend">Tendance (déclinant en premier)</option>
          </select>
        </div>
      </div>

      {/* Documents Table */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Document
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Public
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Récupérations
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Taux de Citation
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Satisfaction
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Tendance
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {sortedDocuments.map((doc, index) => (
                <motion.tr
                  key={doc.id}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.05 }}
                  className="hover:bg-gray-50"
                >
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <div className={`p-2 rounded-full ${getStatusColor(doc.status)}`}>
                        {getStatusIcon(doc.status)}
                      </div>
                      <div className="ml-3">
                        <div className="text-sm font-medium text-gray-900">{doc.name}</div>
                        <div className="text-sm text-gray-500">{doc.userInteractions} interactions</div>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                      doc.audience === 'public' ? 'bg-blue-100 text-blue-800' :
                      doc.audience === 'internal' ? 'bg-yellow-100 text-yellow-800' :
                      'bg-green-100 text-green-800'
                    }`}>
                      {doc.audience === 'public' ? 'Public' :
                       doc.audience === 'internal' ? 'Interne' : 'Clients'}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {doc.retrievals.toLocaleString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <span className={`text-sm font-medium ${
                        doc.citationRate >= 60 ? 'text-success-600' :
                        doc.citationRate >= 40 ? 'text-warning-600' :
                        'text-error-600'
                      }`}>
                        {doc.citationRate}%
                      </span>
                      <div className="ml-2 w-16 bg-gray-200 rounded-full h-2">
                        <div
                          className={`h-2 rounded-full ${
                            doc.citationRate >= 60 ? 'bg-success-500' :
                            doc.citationRate >= 40 ? 'bg-warning-500' :
                            'bg-error-500'
                          }`}
                          style={{ width: `${doc.citationRate}%` }}
                        />
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {doc.satisfaction > 0 ? `${doc.satisfaction}%` : 'N/A'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      {doc.trend > 0 ? (
                        <TrendingUp className="w-4 h-4 text-success-500 mr-1" />
                      ) : (
                        <TrendingDown className="w-4 h-4 text-error-500 mr-1" />
                      )}
                      <span className={`text-sm font-medium ${
                        doc.trend > 0 ? 'text-success-600' : 'text-error-600'
                      }`}>
                        {doc.trend > 0 ? '+' : ''}{doc.trend}%
                      </span>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setSelectedDocument(doc)}
                    >
                      Voir Détails
                    </Button>
                  </td>
                </motion.tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Document Detail Modal */}
      {selectedDocument && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="bg-white rounded-lg shadow-xl max-w-4xl w-full mx-4 max-h-[90vh] overflow-y-auto"
          >
            <div className="p-6">
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-lg font-semibold text-gray-900">
                  {selectedDocument.name}
                </h3>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setSelectedDocument(null)}
                >
                  Fermer
                </Button>
              </div>

              {/* Performance Scorecard */}
              <div className="grid grid-cols-5 gap-4 mb-6">
                <div className="text-center p-4 bg-gray-50 rounded-lg">
                  <div className="text-2xl font-bold text-gray-900">
                    {selectedDocument.retrievals.toLocaleString()}
                  </div>
                  <div className="text-sm text-gray-600">Récupérations</div>
                </div>
                <div className="text-center p-4 bg-gray-50 rounded-lg">
                  <div className="text-2xl font-bold text-gray-900">
                    {selectedDocument.citationRate}%
                  </div>
                  <div className="text-sm text-gray-600">Taux de Citation</div>
                </div>
                <div className="text-center p-4 bg-gray-50 rounded-lg">
                  <div className="text-2xl font-bold text-gray-900">
                    {selectedDocument.satisfaction}%
                  </div>
                  <div className="text-sm text-gray-600">Satisfaction</div>
                </div>
                <div className="text-center p-4 bg-gray-50 rounded-lg">
                  <div className="text-2xl font-bold text-gray-900">
                    {selectedDocument.userInteractions}
                  </div>
                  <div className="text-sm text-gray-600">Clics</div>
                </div>
                <div className="text-center p-4 bg-gray-50 rounded-lg">
                  <div className={`text-2xl font-bold ${
                    selectedDocument.trend > 0 ? 'text-success-600' : 'text-error-600'
                  }`}>
                    {selectedDocument.trend > 0 ? '+' : ''}{selectedDocument.trend}%
                  </div>
                  <div className="text-sm text-gray-600">Tendance</div>
                </div>
              </div>

              {/* Insights Panel */}
              <div className="bg-blue-50 p-4 rounded-lg mb-6">
                <h4 className="font-medium text-blue-900 mb-2">Insights</h4>
                <ul className="text-sm text-blue-800 space-y-1">
                  <li>• Pic d'utilisation au printemps (mars-mai)</li>
                  <li>• Public principal: Agriculteurs posant des questions pratiques</li>
                  <li>• Considérer l'ajout de directives météo (45% des utilisateurs ont aussi recherché ceci)</li>
                </ul>
              </div>

              {/* Source Attribution Analytics Section */}
              <div className="border-t border-gray-200 pt-6">
                <h4 className="text-lg font-medium text-gray-900 mb-4">Source Attribution - Analyse de Performance</h4>
                <p className="text-sm text-gray-600 mb-4">
                  Testez une requête pour analyser comment ce document contribue aux réponses et identifier les opportunités d'amélioration.
                </p>
                
                <div className="space-y-4">
                  <div className="flex space-x-3">
                    <input
                      type="text"
                      value={sourceAttributionQuery}
                      onChange={(e) => setSourceAttributionQuery(e.target.value)}
                      placeholder="Ex: Comment appliquer Roundup correctement?"
                      className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                    <Button
                      onClick={handleSourceAttribution}
                      disabled={!sourceAttributionQuery.trim() || attributionLoading}
                      className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                    >
                      {attributionLoading ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : (
                        <Target className="h-4 w-4" />
                      )}
                      Analyser Performance
                    </Button>
                  </div>

                  {sourceAttribution && (
                    <motion.div
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      className="bg-gray-50 rounded-lg p-4 space-y-4"
                    >
                      <div className="flex items-center space-x-2">
                        <Zap className="h-5 w-5 text-blue-600" />
                        <h5 className="font-medium text-gray-900">Analyse de Performance Source</h5>
                      </div>
                      
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div className="bg-white p-3 rounded-lg">
                          <p className="text-sm text-gray-600">Confiance globale</p>
                          <p className="text-xl font-bold text-blue-600">
                            {Math.round((sourceAttribution.overall_confidence || 0) * 100)}%
                          </p>
                        </div>
                        <div className="bg-white p-3 rounded-lg">
                          <p className="text-sm text-gray-600">Sources trouvées</p>
                          <p className="text-xl font-bold text-green-600">
                            {sourceAttribution.total_sources || 0}
                          </p>
                        </div>
                        <div className="bg-white p-3 rounded-lg">
                          <p className="text-sm text-gray-600">Performance</p>
                          <p className={`text-sm font-medium ${
                            (sourceAttribution.overall_confidence || 0) > 0.7 ? 'text-green-600' :
                            (sourceAttribution.overall_confidence || 0) > 0.4 ? 'text-yellow-600' :
                            'text-red-600'
                          }`}>
                            {(sourceAttribution.overall_confidence || 0) > 0.7 ? 'Excellent' :
                             (sourceAttribution.overall_confidence || 0) > 0.4 ? 'Moyen' : 'Faible'}
                          </p>
                        </div>
                      </div>

                      {sourceAttribution.sources && sourceAttribution.sources.length > 0 && (
                        <div className="space-y-3">
                          <h6 className="font-medium text-gray-900">Analyse des Sources:</h6>
                          {sourceAttribution.sources.map((source: any, index: number) => (
                            <div key={index} className="bg-white p-3 rounded-lg border">
                              <div className="flex items-start justify-between mb-2">
                                <div>
                                  <p className="font-medium text-sm">{source.filename}</p>
                                  <p className="text-xs text-gray-600">
                                    {source.page_info?.page_number && `Page ${source.page_info.page_number}`}
                                    {source.page_info?.section && ` • ${source.page_info.section}`}
                                  </p>
                                </div>
                                <div className="text-right">
                                  <p className="text-sm font-medium text-blue-600">
                                    {Math.round((source.relevance_score || 0) * 100)}%
                                  </p>
                                  <p className="text-xs text-gray-500">Pertinence</p>
                                </div>
                              </div>
                              <p className="text-sm text-gray-700 bg-gray-50 p-2 rounded">
                                {source.text_preview}
                              </p>
                            </div>
                          ))}
                        </div>
                      )}

                      {/* Performance Insights */}
                      <div className="bg-blue-50 p-3 rounded-lg">
                        <h6 className="font-medium text-blue-900 mb-2">Insights de Performance</h6>
                        <ul className="text-sm text-blue-800 space-y-1">
                          {(sourceAttribution.overall_confidence || 0) > 0.7 ? (
                            <>
                              <li>• Excellent alignement avec la requête</li>
                              <li>• Le document fournit des réponses pertinentes</li>
                              <li>• Continuer à promouvoir ce contenu</li>
                            </>
                          ) : (sourceAttribution.overall_confidence || 0) > 0.4 ? (
                            <>
                              <li>• Alignement modéré avec la requête</li>
                              <li>• Considérer l'amélioration du contenu</li>
                              <li>• Ajouter des exemples plus spécifiques</li>
                            </>
                          ) : (
                            <>
                              <li>• Faible alignement avec la requête</li>
                              <li>• Le document pourrait ne pas être optimal pour ce type de questions</li>
                              <li>• Considérer la révision du contenu ou la création de nouveau contenu</li>
                            </>
                          )}
                        </ul>
                      </div>
                    </motion.div>
                  )}
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      )}
    </div>
  )
}

export default PerformanceTab
