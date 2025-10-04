import React, { useState } from 'react'
import { motion } from 'framer-motion'
import { 
  Target, 
  AlertTriangle, 
  Clock, 
  Calendar,
  Users,
  TrendingUp,
  FileText,
  Plus,
  Eye,
  X,
  GripVertical
} from 'lucide-react'

// Components
import { Button } from '@components/ui/Button'

interface ContentGap {
  id: string
  title: string
  queries: number
  dueDate: string
  audience: string
  priority: 'high' | 'medium' | 'low'
  growth: number
  examples: string[]
}

interface DocumentAlert {
  id: string
  documentName: string
  problem: string
  severity: 'urgent' | 'warning' | 'info'
  suggestedFix: string
  citationRate?: number
}

interface RoadmapItem {
  id: string
  title: string
  impact: number
  dueDate: string
  status: 'not-started' | 'in-progress' | 'completed'
  category: 'immediate' | 'short-term' | 'strategic'
}

const ActionPlanTab: React.FC = () => {
  const [selectedGap, setSelectedGap] = useState<ContentGap | null>(null)

  // Mock data - will be replaced with real API calls
  const contentGaps: ContentGap[] = [
    {
      id: '1',
      title: 'Glyphosate en conditions humides',
      queries: 47,
      dueDate: '2024-02-01',
      audience: 'Agriculteurs',
      priority: 'high',
      growth: 89,
      examples: [
        'Comment appliquer Roundup par temps humide ?',
        'Glyphosate efficace sous la pluie ?',
        'Conditions optimales Roundup'
      ]
    },
    {
      id: '2',
      title: 'Compatibilité mélange cuve',
      queries: 34,
      dueDate: '2024-02-15',
      audience: 'Agronomes',
      priority: 'high',
      growth: 67,
      examples: [
        'Peut-on mélanger Roundup et fongicide ?',
        'Incompatibilités produits phytosanitaires',
        'Ordre de mélange cuve'
      ]
    },
    {
      id: '3',
      title: 'Calcul ZNT pentes',
      queries: 28,
      dueDate: '2024-03-01',
      audience: 'Agriculteurs',
      priority: 'medium',
      growth: 45,
      examples: [
        'ZNT sur terrain en pente',
        'Calcul distance pente 10%',
        'Réglementation ZNT pentes'
      ]
    }
  ]

  const documentAlerts: DocumentAlert[] = [
    {
      id: '1',
      documentName: 'Checklist ZNT',
      problem: 'Taux de citation faible',
      severity: 'urgent',
      suggestedFix: 'Ajouter des exemples spécifiques et des calculs',
      citationRate: 12
    },
    {
      id: '2',
      documentName: 'Guide Mélange Produits',
      problem: 'Baisse de performance',
      severity: 'warning',
      suggestedFix: 'Mettre à jour avec les nouvelles réglementations'
    },
    {
      id: '3',
      documentName: 'Formation Sécurité',
      problem: 'Contenu obsolète',
      severity: 'info',
      suggestedFix: 'Réviser les procédures de sécurité 2024'
    }
  ]

  const roadmapItems: RoadmapItem[] = [
    {
      id: '1',
      title: 'Guide Conditions Humides',
      impact: 47,
      dueDate: '2024-02-01',
      status: 'not-started',
      category: 'immediate'
    },
    {
      id: '2',
      title: 'Mise à jour ZNT',
      impact: 28,
      dueDate: '2024-02-15',
      status: 'in-progress',
      category: 'immediate'
    },
    {
      id: '3',
      title: 'Compatibilité Mélanges',
      impact: 34,
      dueDate: '2024-03-01',
      status: 'not-started',
      category: 'short-term'
    },
    {
      id: '4',
      title: 'Stratégies Fongicides Blé',
      impact: 23,
      dueDate: '2024-04-01',
      status: 'not-started',
      category: 'strategic'
    }
  ]

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high': return 'text-error-600 bg-error-50'
      case 'medium': return 'text-warning-600 bg-warning-50'
      case 'low': return 'text-info-600 bg-info-50'
      default: return 'text-gray-600 bg-gray-50'
    }
  }

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'urgent': return 'text-error-600 bg-error-50'
      case 'warning': return 'text-warning-600 bg-warning-50'
      case 'info': return 'text-info-600 bg-info-50'
      default: return 'text-gray-600 bg-gray-50'
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'text-success-600 bg-success-50'
      case 'in-progress': return 'text-warning-600 bg-warning-50'
      case 'not-started': return 'text-gray-600 bg-gray-50'
      default: return 'text-gray-600 bg-gray-50'
    }
  }

  const getCategoryItems = (category: string) => {
    return roadmapItems.filter(item => item.category === category)
  }

  return (
    <div className="space-y-6">
      {/* Priority Matrix */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Matrice de Priorité</h3>
          <Target className="w-5 h-5 text-gray-400" />
        </div>
        
        <div className="grid grid-cols-2 gap-4 h-64">
          <div className="border-2 border-dashed border-gray-300 rounded-lg p-4 flex flex-col justify-center items-center">
            <div className="text-sm font-medium text-gray-600 mb-2">Effort Élevé</div>
            <div className="text-xs text-gray-500 text-center">
              Projets Majeurs<br />
              Planifier pour plus tard
            </div>
          </div>
          <div className="border-2 border-dashed border-gray-300 rounded-lg p-4 flex flex-col justify-center items-center">
            <div className="text-sm font-medium text-gray-600 mb-2">Effort Faible</div>
            <div className="text-xs text-gray-500 text-center">
              Gains Rapides<br />
              FAIRE EN PREMIER
            </div>
          </div>
          <div className="border-2 border-dashed border-gray-300 rounded-lg p-4 flex flex-col justify-center items-center">
            <div className="text-sm font-medium text-gray-600 mb-2">Impact Faible</div>
            <div className="text-xs text-gray-500 text-center">
              Priorité Basse<br />
              Éviter si possible
            </div>
          </div>
          <div className="border-2 border-dashed border-gray-300 rounded-lg p-4 flex flex-col justify-center items-center">
            <div className="text-sm font-medium text-gray-600 mb-2">Impact Élevé</div>
            <div className="text-xs text-gray-500 text-center">
              Projets Majeurs<br />
              Planifier soigneusement
            </div>
          </div>
        </div>
      </div>

      {/* Content Gaps */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Lacunes de Contenu</h3>
          <Plus className="w-5 h-5 text-gray-400" />
        </div>
        
        <div className="space-y-4">
          {contentGaps.map((gap, index) => (
            <motion.div
              key={gap.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
              className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
            >
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-3 mb-2">
                    <h4 className="font-medium text-gray-900">{gap.title}</h4>
                    <span className={`px-2 py-1 text-xs font-semibold rounded-full ${getPriorityColor(gap.priority)}`}>
                      {gap.priority === 'high' ? 'Priorité 1' : gap.priority === 'medium' ? 'Priorité 2' : 'Priorité 3'}
                    </span>
                  </div>
                  
                  <div className="flex items-center space-x-4 text-sm text-gray-600">
                    <div className="flex items-center">
                      <TrendingUp className="w-4 h-4 mr-1" />
                      {gap.queries} requêtes/mois
                    </div>
                    <div className="flex items-center">
                      <Clock className="w-4 h-4 mr-1" />
                      Échéance: {new Date(gap.dueDate).toLocaleDateString('fr-FR')}
                    </div>
                    <div className="flex items-center">
                      <Users className="w-4 h-4 mr-1" />
                      {gap.audience}
                    </div>
                    <div className="flex items-center">
                      <Target className="w-4 h-4 mr-1" />
                      Croissance: +{gap.growth}%
                    </div>
                  </div>
                </div>
                
                <div className="flex items-center space-x-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setSelectedGap(gap)}
                  >
                    <Eye className="w-4 h-4 mr-1" />
                    Voir Détails
                  </Button>
                  <Button size="sm">
                    Créer Contenu
                  </Button>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </div>

      {/* Document Health Alerts */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Alertes Santé Documents</h3>
          <AlertTriangle className="w-5 h-5 text-gray-400" />
        </div>
        
        <div className="space-y-4">
          {documentAlerts.map((alert, index) => (
            <motion.div
              key={alert.id}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.1 }}
              className="border border-gray-200 rounded-lg p-4"
            >
              <div className="flex items-start justify-between">
                <div className="flex items-start space-x-3">
                  <div className={`p-2 rounded-full ${getSeverityColor(alert.severity)}`}>
                    <AlertTriangle className="w-4 h-4" />
                  </div>
                  <div>
                    <div className="flex items-center space-x-2 mb-1">
                      <h4 className="font-medium text-gray-900">{alert.documentName}</h4>
                      <span className={`px-2 py-1 text-xs font-semibold rounded-full ${getSeverityColor(alert.severity)}`}>
                        {alert.severity === 'urgent' ? 'URGENT' : alert.severity === 'warning' ? 'ATTENTION' : 'INFO'}
                      </span>
                    </div>
                    <p className="text-sm text-gray-600 mb-2">{alert.problem}</p>
                    {alert.citationRate && (
                      <p className="text-sm text-gray-500">
                        Taux de citation: {alert.citationRate}% (objectif: 60%+)
                      </p>
                    )}
                    <p className="text-sm text-gray-700 mt-2">
                      <strong>Solution suggérée:</strong> {alert.suggestedFix}
                    </p>
                  </div>
                </div>
                
                <div className="flex items-center space-x-2">
                  <Button variant="outline" size="sm">
                    Voir Document
                  </Button>
                  <Button variant="outline" size="sm">
                    <X className="w-4 h-4" />
                  </Button>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </div>

      {/* Seasonal Forecast */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Prévision Saisonnière</h3>
          <Calendar className="w-5 h-5 text-gray-400" />
        </div>
        
        <div className="space-y-4">
          <div className="flex items-center justify-between text-sm">
            <span className="text-gray-600">Jan</span>
            <span className="text-gray-600">Fév</span>
            <span className="text-gray-600">Mar</span>
            <span className="text-gray-600">Avr</span>
            <span className="text-gray-600">Mai</span>
            <span className="text-gray-600">Jun</span>
            <span className="text-gray-600">Jul</span>
            <span className="text-gray-600">Aoû</span>
            <span className="text-gray-600">Sep</span>
            <span className="text-gray-600">Oct</span>
            <span className="text-gray-600">Nov</span>
            <span className="text-gray-600">Déc</span>
          </div>
          
          <div className="relative h-8 bg-gray-100 rounded-lg overflow-hidden">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full h-2 bg-gray-200 rounded-full">
                <div className="h-full bg-primary-500 rounded-full" style={{ width: '25%' }} />
              </div>
            </div>
            <div className="absolute top-0 left-1/4 w-1/2 h-full bg-warning-200 border-2 border-warning-400 rounded-lg flex items-center justify-center">
              <span className="text-xs font-medium text-warning-800">PIC PRINTEMPS 3x</span>
            </div>
          </div>
          
          <div className="flex items-center justify-between text-xs text-gray-500">
            <span>Mise à jour avant le 1er février</span>
            <span>Préparation saisonnière</span>
          </div>
        </div>
      </div>

      {/* Content Roadmap */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Feuille de Route Contenu</h3>
          <FileText className="w-5 h-5 text-gray-400" />
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Immediate */}
          <div>
            <h4 className="font-medium text-gray-900 mb-3">Immédiat (0-30 jours)</h4>
            <div className="space-y-3">
              {getCategoryItems('immediate').map((item, index) => (
                <motion.div
                  key={item.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.1 }}
                  className="border border-gray-200 rounded-lg p-3"
                >
                  <div className="flex items-start justify-between mb-2">
                    <h5 className="font-medium text-gray-900 text-sm">{item.title}</h5>
                    <GripVertical className="w-4 h-4 text-gray-400" />
                  </div>
                  <div className="flex items-center justify-between text-xs text-gray-600">
                    <span>{item.impact} requêtes/mois</span>
                    <span className={`px-2 py-1 rounded-full ${getStatusColor(item.status)}`}>
                      {item.status === 'not-started' ? 'Non démarré' :
                       item.status === 'in-progress' ? 'En cours' : 'Terminé'}
                    </span>
                  </div>
                  <div className="text-xs text-gray-500 mt-1">
                    Échéance: {new Date(item.dueDate).toLocaleDateString('fr-FR')}
                  </div>
                </motion.div>
              ))}
            </div>
          </div>

          {/* Short-term */}
          <div>
            <h4 className="font-medium text-gray-900 mb-3">Court terme (1-3 mois)</h4>
            <div className="space-y-3">
              {getCategoryItems('short-term').map((item, index) => (
                <motion.div
                  key={item.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.1 }}
                  className="border border-gray-200 rounded-lg p-3"
                >
                  <div className="flex items-start justify-between mb-2">
                    <h5 className="font-medium text-gray-900 text-sm">{item.title}</h5>
                    <GripVertical className="w-4 h-4 text-gray-400" />
                  </div>
                  <div className="flex items-center justify-between text-xs text-gray-600">
                    <span>{item.impact} requêtes/mois</span>
                    <span className={`px-2 py-1 rounded-full ${getStatusColor(item.status)}`}>
                      {item.status === 'not-started' ? 'Non démarré' :
                       item.status === 'in-progress' ? 'En cours' : 'Terminé'}
                    </span>
                  </div>
                  <div className="text-xs text-gray-500 mt-1">
                    Échéance: {new Date(item.dueDate).toLocaleDateString('fr-FR')}
                  </div>
                </motion.div>
              ))}
            </div>
          </div>

          {/* Strategic */}
          <div>
            <h4 className="font-medium text-gray-900 mb-3">Stratégique (3-6 mois)</h4>
            <div className="space-y-3">
              {getCategoryItems('strategic').map((item, index) => (
                <motion.div
                  key={item.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.1 }}
                  className="border border-gray-200 rounded-lg p-3"
                >
                  <div className="flex items-start justify-between mb-2">
                    <h5 className="font-medium text-gray-900 text-sm">{item.title}</h5>
                    <GripVertical className="w-4 h-4 text-gray-400" />
                  </div>
                  <div className="flex items-center justify-between text-xs text-gray-600">
                    <span>{item.impact} requêtes/mois</span>
                    <span className={`px-2 py-1 rounded-full ${getStatusColor(item.status)}`}>
                      {item.status === 'not-started' ? 'Non démarré' :
                       item.status === 'in-progress' ? 'En cours' : 'Terminé'}
                    </span>
                  </div>
                  <div className="text-xs text-gray-500 mt-1">
                    Échéance: {new Date(item.dueDate).toLocaleDateString('fr-FR')}
                  </div>
                </motion.div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Content Gap Detail Modal */}
      {selectedGap && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto"
          >
            <div className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-900">{selectedGap.title}</h3>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setSelectedGap(null)}
                >
                  Fermer
                </Button>
              </div>
              
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="p-4 bg-gray-50 rounded-lg">
                    <div className="text-2xl font-bold text-gray-900">{selectedGap.queries}</div>
                    <div className="text-sm text-gray-600">Requêtes/mois</div>
                  </div>
                  <div className="p-4 bg-gray-50 rounded-lg">
                    <div className="text-2xl font-bold text-gray-900">+{selectedGap.growth}%</div>
                    <div className="text-sm text-gray-600">Croissance</div>
                  </div>
                </div>
                
                <div>
                  <h4 className="font-medium text-gray-900 mb-2">Exemples de questions utilisateurs</h4>
                  <ul className="text-sm text-gray-600 space-y-1">
                    {selectedGap.examples.map((example, index) => (
                      <li key={index}>• "{example}"</li>
                    ))}
                  </ul>
                </div>
                
                <div>
                  <h4 className="font-medium text-gray-900 mb-2">Documents existants liés</h4>
                  <div className="text-sm text-gray-600">
                    Aucun document ne couvre actuellement ce sujet de manière complète.
                  </div>
                </div>
                
                <div>
                  <h4 className="font-medium text-gray-900 mb-2">Titre et plan suggérés</h4>
                  <div className="text-sm text-gray-600">
                    <strong>Titre:</strong> "{selectedGap.title}"<br />
                    <strong>Plan:</strong> Introduction → Conditions → Méthodes → Exemples → Sécurité
                  </div>
                </div>
                
                <div className="flex justify-end space-x-2">
                  <Button variant="outline">Annuler</Button>
                  <Button>Créer ce contenu</Button>
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      )}
    </div>
  )
}

export default ActionPlanTab
