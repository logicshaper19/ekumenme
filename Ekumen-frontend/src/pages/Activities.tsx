import React, { useState, useEffect } from 'react'
import { Calendar, MapPin, Clock, Filter, Search, Download, Eye, BarChart3, TrendingUp, Activity, Loader2, AlertCircle } from 'lucide-react'
import { farmApi, InterventionResponse } from '../services/farmApi'

interface Activity {
  id: string
  date: Date
  parcelle: string
  culture: string
  intervention: string
  produits?: string[]
  surface: number
  cout?: number
  operateur: string
  statut: 'planifie' | 'en_cours' | 'termine' | 'reporte'
  notes?: string
}

const Activities: React.FC = () => {
  const [activities, setActivities] = useState<Activity[]>([])
  const [filteredActivities, setFilteredActivities] = useState<Activity[]>([])
  const [searchTerm, setSearchTerm] = useState('')
  const [filterStatus, setFilterStatus] = useState<string>('all')
  const [filterPeriod, setFilterPeriod] = useState<string>('month')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Load activities from API
  useEffect(() => {
    const loadActivities = async () => {
      try {
        setLoading(true)
        setError(null)
        
        // Fetch interventions from API
        const response = await farmApi.interventions.getInterventions({ limit: 1000 })
        
        // Transform API response to frontend format
        const transformedActivities: Activity[] = response.items.map(apiIntervention => ({
          id: apiIntervention.id,
          date: new Date(apiIntervention.date_intervention),
          parcelle: `Parcelle ${apiIntervention.parcelle_id.slice(-4)}`, // Use last 4 chars of parcelle ID
          culture: 'Non renseigné', // Could be enhanced with parcelle data
          intervention: apiIntervention.type_intervention || 'Intervention',
          produits: apiIntervention.produit_utilise ? [apiIntervention.produit_utilise] : undefined,
          surface: apiIntervention.surface_traitee_ha || 0,
          cout: apiIntervention.cout_total || undefined,
          operateur: 'Non renseigné', // Could be enhanced with user data
          statut: determineActivityStatus(apiIntervention),
          notes: apiIntervention.notes || undefined
        }))
        
        setActivities(transformedActivities)
        setFilteredActivities(transformedActivities)
      } catch (err) {
        console.error('Error loading activities:', err)
        setError(err instanceof Error ? err.message : 'Erreur lors du chargement des activités')
      } finally {
        setLoading(false)
      }
    }

    loadActivities()
  }, [])

  // Helper function to determine activity status
  const determineActivityStatus = (apiIntervention: InterventionResponse): 'planifie' | 'en_cours' | 'termine' | 'reporte' => {
    const interventionDate = new Date(apiIntervention.date_intervention)
    const now = new Date()
    const daysDiff = Math.floor((now.getTime() - interventionDate.getTime()) / (1000 * 60 * 60 * 24))
    
    if (daysDiff < 0) {
      return 'planifie' // Future intervention
    } else if (daysDiff === 0) {
      return 'en_cours' // Today's intervention
    } else {
      return 'termine' // Past intervention
    }
  }

  // Mock data from MesParcelles (commented out - now using real API)
  /*
  useEffect(() => {
    const mockActivities: Activity[] = [
      {
        id: '1',
        date: new Date('2024-01-15'),
        parcelle: 'Parcelle Nord',
        culture: 'Blé tendre',
        intervention: 'Traitement fongicide',
        produits: ['Prosaro', 'Huile de colza'],
        surface: 12.5,
        cout: 156.80,
        operateur: 'Jean Dupont',
        statut: 'termine',
        notes: 'Conditions météo favorables'
      },
      {
        id: '2',
        date: new Date('2024-01-14'),
        parcelle: 'Parcelle Sud',
        culture: 'Colza',
        intervention: 'Semis',
        surface: 8.2,
        cout: 245.60,
        operateur: 'Marie Martin',
        statut: 'termine'
      },
      {
        id: '3',
        date: new Date('2024-01-16'),
        parcelle: 'Parcelle Est',
        culture: 'Orge',
        intervention: 'Fertilisation',
        produits: ['Ammonitrate 33.5'],
        surface: 15.0,
        cout: 320.00,
        operateur: 'Jean Dupont',
        statut: 'planifie'
      },
      {
        id: '4',
        date: new Date('2024-01-13'),
        parcelle: 'Parcelle Ouest',
        culture: 'Blé tendre',
        intervention: 'Désherbage',
        produits: ['Atlantis WG', 'Actirob B'],
        surface: 10.8,
        cout: 198.40,
        operateur: 'Pierre Durand',
        statut: 'en_cours'
      },
      {
        id: '5',
        date: new Date('2024-01-12'),
        parcelle: 'Parcelle Centre',
        culture: 'Tournesol',
        intervention: 'Travail du sol',
        surface: 6.5,
        cout: 89.50,
        operateur: 'Marie Martin',
        statut: 'reporte',
        notes: 'Reporté à cause de la pluie'
      }
    ]
    setActivities(mockActivities)
    setFilteredActivities(mockActivities)
  }, [])
  */

  // Filter activities
  useEffect(() => {
    let filtered = activities

    // Filter by search term
    if (searchTerm) {
      filtered = filtered.filter(activity =>
        activity.parcelle.toLowerCase().includes(searchTerm.toLowerCase()) ||
        activity.culture.toLowerCase().includes(searchTerm.toLowerCase()) ||
        activity.intervention.toLowerCase().includes(searchTerm.toLowerCase()) ||
        activity.operateur.toLowerCase().includes(searchTerm.toLowerCase())
      )
    }

    // Filter by status
    if (filterStatus !== 'all') {
      filtered = filtered.filter(activity => activity.statut === filterStatus)
    }

    // Filter by period
    const now = new Date()
    if (filterPeriod === 'week') {
      const weekAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000)
      filtered = filtered.filter(activity => activity.date >= weekAgo)
    } else if (filterPeriod === 'month') {
      const monthAgo = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000)
      filtered = filtered.filter(activity => activity.date >= monthAgo)
    }

    setFilteredActivities(filtered)
  }, [activities, searchTerm, filterStatus, filterPeriod])

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'termine': return 'bg-green-100 text-green-800'
      case 'en_cours': return 'bg-blue-100 text-blue-800'
      case 'planifie': return 'bg-yellow-100 text-yellow-800'
      case 'reporte': return 'bg-red-100 text-red-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const getStatusText = (status: string) => {
    switch (status) {
      case 'termine': return 'Terminé'
      case 'en_cours': return 'En cours'
      case 'planifie': return 'Planifié'
      case 'reporte': return 'Reporté'
      default: return status
    }
  }

  const formatDate = (date: Date) => {
    return date.toLocaleDateString('fr-FR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric'
    })
  }

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('fr-FR', {
      style: 'currency',
      currency: 'EUR'
    }).format(amount)
  }

  const totalCost = filteredActivities.reduce((sum, activity) => sum + (activity.cout || 0), 0)
  const totalSurface = filteredActivities.reduce((sum, activity) => sum + activity.surface, 0)

  return (
    <div className="space-y-6 p-6">
      <div>
        <h1 className="text-2xl font-bold text-primary">Activités Agricoles</h1>
        <p className="mt-1 text-sm text-secondary">
          Historique des interventions et activités sur vos parcelles
        </p>
      </div>

      {/* Loading State */}
      {loading && (
        <div className="flex items-center justify-center py-12">
          <div className="flex items-center space-x-2">
            <Loader2 className="h-6 w-6 animate-spin text-primary" />
            <span className="text-secondary">Chargement des activités...</span>
          </div>
        </div>
      )}

      {/* Error State */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center space-x-2">
            <AlertCircle className="h-5 w-5 text-red-500" />
            <span className="text-red-700 font-medium">Erreur</span>
          </div>
          <p className="text-red-600 mt-1">{error}</p>
        </div>
      )}

      {/* Content - only show when not loading and no error */}
      {!loading && !error && (
        <>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="card p-4">
          <div className="text-2xl font-bold text-primary">{filteredActivities.length}</div>
          <div className="text-sm text-secondary">Activités</div>
        </div>
        <div className="card p-4">
          <div className="text-2xl font-bold text-success">{totalSurface.toFixed(1)} ha</div>
          <div className="text-sm text-secondary">Surface totale</div>
        </div>
        <div className="card p-4">
          <div className="text-2xl font-bold text-blue-600">{formatCurrency(totalCost)}</div>
          <div className="text-sm text-secondary">Coût total</div>
        </div>
        <div className="card p-4">
          <div className="text-2xl font-bold text-warning">
            {filteredActivities.filter(a => a.statut === 'planifie').length}
          </div>
          <div className="text-sm text-secondary">Planifiées</div>
        </div>
      </div>

      {/* Filters */}
      <div className="card p-4">
        <div className="flex flex-col md:flex-row gap-4">
          {/* Search */}
          <div className="flex-1">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted" />
              <input
                type="text"
                placeholder="Rechercher par parcelle, culture, intervention..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="input pl-10"
              />
            </div>
          </div>

          {/* Status Filter */}
          <div>
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="input"
            >
              <option value="all">Tous les statuts</option>
              <option value="termine">Terminé</option>
              <option value="en_cours">En cours</option>
              <option value="planifie">Planifié</option>
              <option value="reporte">Reporté</option>
            </select>
          </div>

          {/* Period Filter */}
          <div>
            <select
              value={filterPeriod}
              onChange={(e) => setFilterPeriod(e.target.value)}
              className="input"
            >
              <option value="all">Toute la période</option>
              <option value="week">7 derniers jours</option>
              <option value="month">30 derniers jours</option>
            </select>
          </div>

          {/* Export Button */}
          <button className="btn-primary">
            <Download className="h-4 w-4" />
            Exporter
          </button>
        </div>
      </div>

      {/* Analytics Overview */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
        <div className="card p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-muted">Total Activités</p>
              <p className="text-2xl font-bold text-primary">{activities.length}</p>
              <p className="text-xs text-success flex items-center mt-1">
                <TrendingUp className="h-3 w-3 mr-1" />
                +8% ce mois
              </p>
            </div>
            <div className="p-3 bg-primary/10 rounded-lg">
              <Activity className="h-6 w-6 text-primary" />
            </div>
          </div>
        </div>

        <div className="card p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-muted">Surface Totale</p>
              <p className="text-2xl font-bold text-primary">
                {activities.reduce((sum, activity) => sum + activity.surface, 0).toFixed(1)} ha
              </p>
              <p className="text-xs text-muted mt-1">
                Moyenne: {(activities.reduce((sum, activity) => sum + activity.surface, 0) / activities.length).toFixed(1)} ha/activité
              </p>
            </div>
            <div className="p-3 bg-green-100 rounded-lg">
              <MapPin className="h-6 w-6 text-green-600" />
            </div>
          </div>
        </div>

        <div className="card p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-muted">Coût Total</p>
              <p className="text-2xl font-bold text-primary">
                {formatCurrency(activities.reduce((sum, activity) => sum + (activity.cout || 0), 0))}
              </p>
              <p className="text-xs text-muted mt-1">
                Moyenne: {formatCurrency(activities.reduce((sum, activity) => sum + (activity.cout || 0), 0) / activities.length)}
              </p>
            </div>
            <div className="p-3 bg-blue-100 rounded-lg">
              <BarChart3 className="h-6 w-6 text-blue-600" />
            </div>
          </div>
        </div>
      </div>

      {/* Activities List */}
      <div className="card">
        <div className="px-6 py-4 border-b border-subtle">
          <h2 className="text-lg font-semibold text-primary">Liste des Activités</h2>
        </div>

        <div className="divide-y divide-subtle">
          {filteredActivities.length === 0 ? (
            <div className="p-8 text-center text-muted">
              <Calendar className="h-12 w-12 mx-auto mb-4 text-muted" />
              <p>Aucune activité trouvée</p>
              <p className="text-sm">Modifiez vos filtres pour voir plus d'activités</p>
            </div>
          ) : (
            filteredActivities.map((activity) => (
              <div key={activity.id} className="p-6 bg-card-hover transition-theme">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-4 mb-2">
                      <div className="flex items-center gap-2 text-sm text-secondary">
                        <Calendar className="h-4 w-4" />
                        <span>{formatDate(activity.date)}</span>
                      </div>

                      <span className={`inline-flex items-center px-2 py-1 text-xs rounded-full ${getStatusColor(activity.statut)}`}>
                        {getStatusText(activity.statut)}
                      </span>
                    </div>

                    <div className="flex items-center gap-2 mb-2">
                      <MapPin className="h-4 w-4 text-muted" />
                      <span className="font-medium text-primary">{activity.parcelle}</span>
                      <span className="text-muted">•</span>
                      <span className="text-secondary">{activity.culture}</span>
                      <span className="text-muted">•</span>
                      <span className="text-secondary">{activity.intervention}</span>
                    </div>

                    {activity.produits && activity.produits.length > 0 && (
                      <div className="mb-2">
                        <span className="text-sm text-secondary">Produits: </span>
                        <span className="text-sm text-primary">{activity.produits.join(', ')}</span>
                      </div>
                    )}

                    <div className="grid grid-cols-1 md:grid-cols-4 gap-4 text-sm text-secondary">
                      <div>
                        <span className="font-medium">Surface:</span> {activity.surface} ha
                      </div>
                      {activity.cout && (
                        <div>
                          <span className="font-medium">Coût:</span> {formatCurrency(activity.cout)}
                        </div>
                      )}
                      <div>
                        <span className="font-medium">Opérateur:</span> {activity.operateur}
                      </div>
                      {activity.notes && (
                        <div>
                          <span className="font-medium">Notes:</span> {activity.notes}
                        </div>
                      )}
                    </div>
                  </div>

                  <div className="flex items-center gap-2 ml-4">
                    <button
                      className="p-2 text-muted hover:text-primary transition-theme"
                      title="Voir détails"
                    >
                      <Eye className="h-4 w-4" />
                    </button>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
        </>
      )}
    </div>
  )
}

export default Activities
