import React, { useState, useEffect } from 'react'
import { MapPin, Crop, Calendar, BarChart3, Eye, Edit, Plus, Search, TrendingUp } from 'lucide-react'
import { farmApi, ParcelleResponse } from '../services/farmApi'
import { useFarmRealtime } from '../services/farmRealtimeService'

// Frontend interface that extends the API response with computed fields
interface Parcelle extends ParcelleResponse {
  // Computed fields for display
  culture_actuelle: string
  surface: number
  statut: 'seme' | 'en_croissance' | 'recolte' | 'jachère'
  irrigation?: boolean
  sol_type?: string
  notes?: string
  coordonnees?: {
    latitude: number
    longitude: number
  }
  date_recolte_prevue?: Date
  rendement_prevu?: number
  rendement_realise?: number
  derniere_intervention?: Date
}

const Parcelles: React.FC = () => {
  const [parcelles, setParcelles] = useState<Parcelle[]>([])
  const [filteredParcelles, setFilteredParcelles] = useState<Parcelle[]>([])
  const [searchTerm, setSearchTerm] = useState('')
  const [filterCulture, setFilterCulture] = useState<string>('all')
  const [filterStatut, setFilterStatut] = useState<string>('all')
  const [showAddModal, setShowAddModal] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  
  // Real-time updates
  const farmRealtime = useFarmRealtime()

  // Helper function to determine parcelle status
  const determineParcelleStatus = (apiParcelle: ParcelleResponse): 'seme' | 'en_croissance' | 'recolte' | 'jachère' => {
    if (!apiParcelle.culture_code || apiParcelle.culture_code === 'JACHERE') {
      return 'jachère'
    }
    
    if (apiParcelle.date_semis) {
      const semisDate = new Date(apiParcelle.date_semis)
      const now = new Date()
      const daysSinceSemis = Math.floor((now.getTime() - semisDate.getTime()) / (1000 * 60 * 60 * 24))
      
      if (daysSinceSemis < 30) {
        return 'seme'
      } else if (daysSinceSemis < 200) {
        return 'en_croissance'
      } else {
        return 'recolte'
      }
    }
    
    return 'en_croissance' // Default status
  }

  // Load parcelles from API
  const loadParcelles = async () => {
    try {
      setLoading(true)
      setError(null)
      
      // Fetch parcelles from API
      const response = await farmApi.parcelles.getParcelles({ limit: 1000 })
      
      // Transform API response to frontend format
      const transformedParcelles: Parcelle[] = response.items.map(apiParcelle => ({
        ...apiParcelle,
        // Map API fields to frontend fields
        culture_actuelle: apiParcelle.culture_code || 'Non renseigné',
        surface: apiParcelle.surface_ha,
        // Determine status based on available data
        statut: determineParcelleStatus(apiParcelle),
        // Add computed fields for display
        irrigation: false, // Default, could be enhanced with real data
        sol_type: 'Non renseigné', // Default, could be enhanced with real data
        notes: apiParcelle.culture_intermediaire ? 'Culture intermédiaire' : undefined,
        // Keep date_semis as string to match API response
        date_semis: apiParcelle.date_semis,
        // Add mock coordinates for display (could be enhanced with real geometry data)
        coordonnees: {
          latitude: 48.8566 + (Math.random() - 0.5) * 0.01,
          longitude: 2.3522 + (Math.random() - 0.5) * 0.01
        }
      }))
      
      setParcelles(transformedParcelles)
      setFilteredParcelles(transformedParcelles)
    } catch (err) {
      console.error('Error loading parcelles:', err)
      setError(err instanceof Error ? err.message : 'Erreur lors du chargement des parcelles')
    } finally {
      setLoading(false)
    }
  }

  // Load parcelles on component mount
  useEffect(() => {
    loadParcelles()
  }, [])

  // Connect to real-time updates
  useEffect(() => {
    // Connect to farm WebSocket
    farmRealtime.connect()

    // Subscribe to parcelle updates
    const subscriptionId = farmRealtime.subscribeToFarm(
      '12345678901234', // farmer@test.com's farm SIRET
      (update) => {
        console.log('Received parcelle update:', update)
        if (update.type === 'parcelle' || update.type === 'intervention') {
          // Reload parcelles when updates are received
          loadParcelles()
        }
      }
    )

    return () => {
      farmRealtime.unsubscribe(subscriptionId)
      farmRealtime.disconnect()
    }
  }, [])

  // Filter parcelles
  useEffect(() => {
    let filtered = parcelles

    // Filter by search term
    if (searchTerm) {
      filtered = filtered.filter(parcelle =>
        parcelle.nom.toLowerCase().includes(searchTerm.toLowerCase()) ||
        parcelle.culture_actuelle.toLowerCase().includes(searchTerm.toLowerCase()) ||
        (parcelle.variete && parcelle.variete.toLowerCase().includes(searchTerm.toLowerCase()))
      )
    }

    // Filter by culture
    if (filterCulture !== 'all') {
      filtered = filtered.filter(parcelle => parcelle.culture_actuelle === filterCulture)
    }

    // Filter by status
    if (filterStatut !== 'all') {
      filtered = filtered.filter(parcelle => parcelle.statut === filterStatut)
    }

    setFilteredParcelles(filtered)
  }, [parcelles, searchTerm, filterCulture, filterStatut])


  const getStatutColor = (statut: string) => {
    switch (statut) {
      case 'seme': return 'bg-blue-100 text-blue-800'
      case 'en_croissance': return 'bg-green-100 text-green-800'
      case 'recolte': return 'bg-yellow-100 text-yellow-800'
      case 'jachère': return 'bg-gray-100 text-gray-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const getStatutText = (statut: string) => {
    switch (statut) {
      case 'seme': return 'Semé'
      case 'en_croissance': return 'En croissance'
      case 'recolte': return 'Récolte'
      case 'jachère': return 'Jachère'
      default: return statut
    }
  }

  const formatDate = (date: Date | string | undefined) => {
    if (!date) return 'Non renseigné'
    const dateObj = typeof date === 'string' ? new Date(date) : date
    return dateObj.toLocaleDateString('fr-FR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric'
    })
  }

  const uniqueCultures = [...new Set(parcelles.map(p => p.culture_actuelle))]
  const totalSurface = filteredParcelles.reduce((sum, parcelle) => sum + parcelle.surface, 0)
  const rendementMoyen = filteredParcelles
    .filter(p => p.rendement_prevu)
    .reduce((sum, p) => sum + (p.rendement_prevu || 0), 0) / 
    filteredParcelles.filter(p => p.rendement_prevu).length || 0

  return (
    <div className="space-y-6 p-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-primary">Gestion des Parcelles</h1>
          <p className="mt-1 text-sm text-secondary">
            Vue d'ensemble de vos parcelles et cultures
          </p>
        </div>
        <button
          onClick={() => setShowAddModal(true)}
          className="btn-primary"
        >
          <Plus className="h-4 w-4" />
          Nouvelle parcelle
        </button>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="card p-4">
          <div className="text-2xl font-bold text-primary">{filteredParcelles.length}</div>
          <div className="text-sm text-secondary">Parcelles</div>
        </div>
        <div className="card p-4">
          <div className="text-2xl font-bold text-success">{totalSurface.toFixed(1)} ha</div>
          <div className="text-sm text-secondary">Surface totale</div>
        </div>
        <div className="card p-4">
          <div className="text-2xl font-bold text-blue-600">{rendementMoyen.toFixed(1)} q/ha</div>
          <div className="text-sm text-secondary">Rendement moyen prévu</div>
        </div>
        <div className="card p-4">
          <div className="text-2xl font-bold text-warning">
            {filteredParcelles.filter(p => p.irrigation).length}
          </div>
          <div className="text-sm text-secondary">Avec irrigation</div>
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
                placeholder="Rechercher par nom, culture, variété..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="input pl-10"
              />
            </div>
          </div>

          {/* Culture Filter */}
          <div>
            <select
              value={filterCulture}
              onChange={(e) => setFilterCulture(e.target.value)}
              className="input"
            >
              <option value="all">Toutes les cultures</option>
              {uniqueCultures.map(culture => (
                <option key={culture} value={culture}>{culture}</option>
              ))}
            </select>
          </div>

          {/* Status Filter */}
          <div>
            <select
              value={filterStatut}
              onChange={(e) => setFilterStatut(e.target.value)}
              className="input"
            >
              <option value="all">Tous les statuts</option>
              <option value="seme">Semé</option>
              <option value="en_croissance">En croissance</option>
              <option value="recolte">Récolte</option>
              <option value="jachère">Jachère</option>
            </select>
          </div>
        </div>
      </div>

      {/* Analytics Overview */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
        <div className="card p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-muted">Total Parcelles</p>
              <p className="text-2xl font-bold text-primary">{parcelles.length}</p>
              <p className="text-xs text-success flex items-center mt-1">
                <TrendingUp className="h-3 w-3 mr-1" />
                +2 nouvelles
              </p>
            </div>
            <div className="p-3 bg-primary/10 rounded-lg">
              <MapPin className="h-6 w-6 text-primary" />
            </div>
          </div>
        </div>

        <div className="card p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-muted">Surface Totale</p>
              <p className="text-2xl font-bold text-primary">
                {parcelles.reduce((sum, parcelle) => sum + parcelle.surface, 0).toFixed(1)} ha
              </p>
              <p className="text-xs text-muted mt-1">
                Moyenne: {(parcelles.reduce((sum, parcelle) => sum + parcelle.surface, 0) / parcelles.length).toFixed(1)} ha/parcelle
              </p>
            </div>
            <div className="p-3 bg-green-100 rounded-lg">
              <BarChart3 className="h-6 w-6 text-green-600" />
            </div>
          </div>
        </div>

        <div className="card p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-muted">Cultures Actives</p>
              <p className="text-2xl font-bold text-primary">
                {new Set(parcelles.map(p => p.culture_actuelle)).size}
              </p>
              <p className="text-xs text-muted mt-1">
                En croissance: {parcelles.filter(p => p.statut === 'en_croissance').length}
              </p>
            </div>
            <div className="p-3 bg-blue-100 rounded-lg">
              <Crop className="h-6 w-6 text-blue-600" />
            </div>
          </div>
        </div>
      </div>

      {/* Parcelles Table */}
      <div className="card overflow-hidden">
        {filteredParcelles.length === 0 ? (
          <div className="p-8 text-center text-muted">
            <MapPin className="h-12 w-12 mx-auto mb-4 text-muted" />
            <p>Aucune parcelle trouvée</p>
            <p className="text-sm">Modifiez vos filtres ou ajoutez une nouvelle parcelle</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-subtle">
              <thead className="bg-card-hover">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-muted uppercase tracking-wider">
                    Parcelle
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-muted uppercase tracking-wider">
                    Culture
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-muted uppercase tracking-wider">
                    Surface
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-muted uppercase tracking-wider">
                    Statut
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-muted uppercase tracking-wider">
                    Rendement prévu
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-muted uppercase tracking-wider">
                    Sol / Irrigation
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-muted uppercase tracking-wider">
                    Dates importantes
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-muted uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-card divide-y divide-subtle">
                {filteredParcelles.map((parcelle) => (
                  <tr key={parcelle.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div>
                        <div className="text-sm font-medium text-gray-900">{parcelle.nom}</div>
                        {parcelle.coordonnees && (
                          <div className="text-xs text-gray-500 flex items-center">
                            <MapPin className="h-3 w-3 mr-1" />
                            {parcelle.coordonnees.latitude.toFixed(4)}, {parcelle.coordonnees.longitude.toFixed(4)}
                          </div>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <Crop className="h-4 w-4 text-green-500 mr-2" />
                        <div>
                          <div className="text-sm font-medium text-gray-900">{parcelle.culture_actuelle}</div>
                          {parcelle.variete && (
                            <div className="text-xs text-gray-500">{parcelle.variete}</div>
                          )}
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900">{parcelle.surface} ha</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatutColor(parcelle.statut)}`}>
                        {getStatutText(parcelle.statut)}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {parcelle.rendement_prevu ? (
                        <div className="flex items-center text-sm text-gray-900">
                          <BarChart3 className="h-4 w-4 text-green-500 mr-1" />
                          {parcelle.rendement_prevu} q/ha
                        </div>
                      ) : (
                        <span className="text-gray-400">-</span>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div>
                        <div className="text-sm text-gray-900">{parcelle.sol_type || 'Non renseigné'}</div>
                        <div className="text-xs text-gray-500">
                          {parcelle.irrigation ? '💧 Irrigué' : '🌧️ Pluvial'}
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-xs text-gray-600 space-y-1">
                        {parcelle.date_semis && (
                          <div className="flex items-center">
                            <Calendar className="h-3 w-3 mr-1" />
                            Semé: {formatDate(parcelle.date_semis)}
                          </div>
                        )}
                        {parcelle.date_recolte_prevue && (
                          <div className="flex items-center">
                            <Calendar className="h-3 w-3 mr-1" />
                            Récolte: {formatDate(parcelle.date_recolte_prevue)}
                          </div>
                        )}
                        {parcelle.derniere_intervention && (
                          <div className="flex items-center">
                            <Calendar className="h-3 w-3 mr-1" />
                            Intervention: {formatDate(parcelle.derniere_intervention)}
                          </div>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <div className="flex justify-end space-x-2">
                        <button className="text-green-600 hover:text-green-700 p-1" title="Voir détails">
                          <Eye className="h-4 w-4" />
                        </button>
                        <button className="text-gray-400 hover:text-gray-600 p-1" title="Modifier">
                          <Edit className="h-4 w-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Add Modal Placeholder */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold">Nouvelle Parcelle</h3>
              <button
                onClick={() => setShowAddModal(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            
            <p className="text-gray-600 mb-4">
              Fonctionnalité d'ajout de parcelle à implémenter
            </p>
            
            <button
              onClick={() => setShowAddModal(false)}
              className="w-full px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
            >
              Fermer
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

export default Parcelles
