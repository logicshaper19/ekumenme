import React, { useState, useEffect } from 'react'
import { Beaker, Calendar, MapPin, AlertTriangle, Search, Filter, Download, Eye, ExternalLink, BarChart3, TrendingUp, Activity, Loader2, AlertCircle } from 'lucide-react'
import { farmApi, InterventionResponse } from '../services/farmApi'

interface Treatment {
  id: string
  date: Date
  parcelle: string
  culture: string
  produit: string
  amm: string
  dose: number
  unite: string
  surface: number
  volume_bouillie: number
  conditions_meteo: string
  operateur: string
  znt?: number
  delai_reentree?: number
  delai_recolte?: number
  notes?: string
}

const Treatments: React.FC = () => {
  const [treatments, setTreatments] = useState<Treatment[]>([])
  const [filteredTreatments, setFilteredTreatments] = useState<Treatment[]>([])
  const [searchTerm, setSearchTerm] = useState('')
  const [filterPeriod, setFilterPeriod] = useState<string>('month')
  const [filterParcelle, setFilterParcelle] = useState<string>('all')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Load treatments from API
  useEffect(() => {
    const loadTreatments = async () => {
      try {
        setLoading(true)
        setError(null)
        
        // Fetch interventions from API
        const response = await farmApi.interventions.getInterventions({ limit: 1000 })
        
        // Transform API response to frontend format
        const transformedTreatments: Treatment[] = response.items.map(apiIntervention => ({
          id: apiIntervention.id,
          date: new Date(apiIntervention.date_intervention),
          parcelle: `Parcelle ${apiIntervention.parcelle_id.slice(-4)}`, // Use last 4 chars of parcelle ID
          culture: 'Non renseigné', // Could be enhanced with parcelle data
          produit: apiIntervention.produit_utilise || 'Non renseigné',
          amm: 'Non renseigné', // Could be enhanced with product data
          dose: apiIntervention.dose_totale || 0,
          unite: apiIntervention.unite_dose || 'L/ha',
          surface: apiIntervention.surface_traitee_ha || 0,
          volume_bouillie: 0, // Could be calculated from dose and surface
          conditions_meteo: apiIntervention.conditions_meteo || 'Non renseigné',
          operateur: 'Non renseigné', // Could be enhanced with user data
          znt: 5, // Default ZNT, could be enhanced with product data
          delai_reentree: 6, // Default, could be enhanced with product data
          delai_recolte: 42, // Default, could be enhanced with product data
          notes: apiIntervention.notes || undefined
        }))
        
        setTreatments(transformedTreatments)
        setFilteredTreatments(transformedTreatments)
      } catch (err) {
        console.error('Error loading treatments:', err)
        setError(err instanceof Error ? err.message : 'Erreur lors du chargement des traitements')
      } finally {
        setLoading(false)
      }
    }

    loadTreatments()
  }, [])

  // Mock data from EPHY database (commented out - now using real API)
  /*
  useEffect(() => {
    const mockTreatments: Treatment[] = [
      {
        id: '1',
        date: new Date('2024-01-15'),
        parcelle: 'Parcelle Nord',
        culture: 'Blé tendre',
        produit: 'Prosaro',
        amm: '2010448',
        dose: 0.8,
        unite: 'L/ha',
        surface: 12.5,
        volume_bouillie: 200,
        conditions_meteo: 'Ensoleillé, 18°C, vent 5 km/h',
        operateur: 'Jean Dupont',
        znt: 5,
        delai_reentree: 6,
        delai_recolte: 35,
        notes: 'Traitement préventif contre la septoriose'
      },
      {
        id: '2',
        date: new Date('2024-01-13'),
        parcelle: 'Parcelle Ouest',
        culture: 'Blé tendre',
        produit: 'Atlantis WG',
        amm: '2050123',
        dose: 0.5,
        unite: 'kg/ha',
        surface: 10.8,
        volume_bouillie: 200,
        conditions_meteo: 'Nuageux, 15°C, vent 8 km/h',
        operateur: 'Pierre Durand',
        znt: 5,
        delai_reentree: 24,
        delai_recolte: 60,
        notes: 'Désherbage post-levée'
      },
      {
        id: '3',
        date: new Date('2024-01-10'),
        parcelle: 'Parcelle Sud',
        culture: 'Colza',
        produit: 'Karaté Zeon',
        amm: '2040567',
        dose: 0.075,
        unite: 'L/ha',
        surface: 8.2,
        volume_bouillie: 150,
        conditions_meteo: 'Ensoleillé, 20°C, vent 3 km/h',
        operateur: 'Marie Martin',
        znt: 20,
        delai_reentree: 24,
        delai_recolte: 60,
        notes: 'Traitement contre les altises'
      },
      {
        id: '4',
        date: new Date('2024-01-08'),
        parcelle: 'Parcelle Est',
        culture: 'Orge',
        produit: 'Opus Team',
        amm: '2030789',
        dose: 1.0,
        unite: 'L/ha',
        surface: 15.0,
        volume_bouillie: 200,
        conditions_meteo: 'Couvert, 12°C, vent 10 km/h',
        operateur: 'Jean Dupont',
        znt: 5,
        delai_reentree: 6,
        delai_recolte: 42,
        notes: 'Fongicide contre l\'oïdium'
      }
    ]
    setTreatments(mockTreatments)
    setFilteredTreatments(mockTreatments)
  }, [])
  */

  // Filter treatments
  useEffect(() => {
    let filtered = treatments

    // Filter by search term
    if (searchTerm) {
      filtered = filtered.filter(treatment =>
        treatment.parcelle.toLowerCase().includes(searchTerm.toLowerCase()) ||
        treatment.culture.toLowerCase().includes(searchTerm.toLowerCase()) ||
        treatment.produit.toLowerCase().includes(searchTerm.toLowerCase()) ||
        treatment.amm.includes(searchTerm) ||
        treatment.operateur.toLowerCase().includes(searchTerm.toLowerCase())
      )
    }

    // Filter by parcelle
    if (filterParcelle !== 'all') {
      filtered = filtered.filter(treatment => treatment.parcelle === filterParcelle)
    }

    // Filter by period
    const now = new Date()
    if (filterPeriod === 'week') {
      const weekAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000)
      filtered = filtered.filter(treatment => treatment.date >= weekAgo)
    } else if (filterPeriod === 'month') {
      const monthAgo = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000)
      filtered = filtered.filter(treatment => treatment.date >= monthAgo)
    }

    setFilteredTreatments(filtered)
  }, [treatments, searchTerm, filterParcelle, filterPeriod])

  const formatDate = (date: Date) => {
    return date.toLocaleDateString('fr-FR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric'
    })
  }

  const getZntColor = (znt?: number) => {
    if (!znt) return 'text-gray-600'
    if (znt >= 20) return 'text-red-600'
    if (znt >= 10) return 'text-yellow-600'
    return 'text-green-600'
  }

  const isDelayRespected = (date: Date, delay?: number) => {
    if (!delay) return true
    const now = new Date()
    const delayDate = new Date(date.getTime() + delay * 24 * 60 * 60 * 1000)
    return now >= delayDate
  }

  const uniqueParcelles = [...new Set(treatments.map(t => t.parcelle))]
  const totalSurface = filteredTreatments.reduce((sum, treatment) => sum + treatment.surface, 0)
  const totalVolume = filteredTreatments.reduce((sum, treatment) => sum + (treatment.dose * treatment.surface), 0)

  return (
    <div className="space-y-6 p-6">
      <div>
        <h1 className="text-2xl font-bold text-primary">Traitements Phytosanitaires</h1>
        <p className="mt-1 text-sm text-secondary">
          Historique des produits phytosanitaires utilisés sur vos parcelles
        </p>
      </div>

      {/* Loading State */}
      {loading && (
        <div className="flex items-center justify-center py-12">
          <div className="flex items-center space-x-2">
            <Loader2 className="h-6 w-6 animate-spin text-primary" />
            <span className="text-secondary">Chargement des traitements...</span>
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
          <div className="text-2xl font-bold text-primary">{filteredTreatments.length}</div>
          <div className="text-sm text-secondary">Traitements</div>
        </div>
        <div className="card p-4">
          <div className="text-2xl font-bold text-success">{totalSurface.toFixed(1)} ha</div>
          <div className="text-sm text-secondary">Surface traitée</div>
        </div>
        <div className="card p-4">
          <div className="text-2xl font-bold text-blue-600">{totalVolume.toFixed(2)} L</div>
          <div className="text-sm text-secondary">Volume total</div>
        </div>
        <div className="card p-4">
          <div className="text-2xl font-bold text-warning">
            {new Set(filteredTreatments.map(t => t.produit)).size}
          </div>
          <div className="text-sm text-secondary">Produits différents</div>
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
                placeholder="Rechercher par produit, AMM, parcelle..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="input pl-10"
              />
            </div>
          </div>

          {/* Parcelle Filter */}
          <div>
            <select
              value={filterParcelle}
              onChange={(e) => setFilterParcelle(e.target.value)}
              className="input"
            >
              <option value="all">Toutes les parcelles</option>
              {uniqueParcelles.map(parcelle => (
                <option key={parcelle} value={parcelle}>{parcelle}</option>
              ))}
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
            Registre
          </button>
        </div>
      </div>

      {/* Analytics Overview */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
        <div className="card p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-muted">Total Traitements</p>
              <p className="text-2xl font-bold text-primary">{treatments.length}</p>
              <p className="text-xs text-success flex items-center mt-1">
                <TrendingUp className="h-3 w-3 mr-1" />
                +12% ce mois
              </p>
            </div>
            <div className="p-3 bg-primary/10 rounded-lg">
              <Beaker className="h-6 w-6 text-primary" />
            </div>
          </div>
        </div>

        <div className="card p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-muted">Surface Totale</p>
              <p className="text-2xl font-bold text-primary">
                {treatments.reduce((sum, treatment) => sum + treatment.surface, 0).toFixed(1)} ha
              </p>
              <p className="text-xs text-muted mt-1">
                Moyenne: {(treatments.reduce((sum, treatment) => sum + treatment.surface, 0) / treatments.length).toFixed(1)} ha/traitement
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
              <p className="text-sm font-medium text-muted">Produits Uniques</p>
              <p className="text-2xl font-bold text-primary">
                {new Set(treatments.map(t => t.produit)).size}
              </p>
              <p className="text-xs text-muted mt-1">
                Moyenne: {(treatments.reduce((sum, treatment) => sum + treatment.dose, 0) / treatments.length).toFixed(1)} L/ha
              </p>
            </div>
            <div className="p-3 bg-blue-100 rounded-lg">
              <BarChart3 className="h-6 w-6 text-blue-600" />
            </div>
          </div>
        </div>
      </div>

      {/* Treatments List */}
      <div className="card">
        <div className="px-6 py-4 border-b border-subtle">
          <h2 className="text-lg font-semibold text-primary">Registre des Traitements</h2>
        </div>

        <div className="divide-y divide-subtle">
          {filteredTreatments.length === 0 ? (
            <div className="p-8 text-center text-muted">
              <Beaker className="h-12 w-12 mx-auto mb-4 text-muted" />
              <p>Aucun traitement trouvé</p>
              <p className="text-sm">Modifiez vos filtres pour voir plus de traitements</p>
            </div>
          ) : (
            filteredTreatments.map((treatment) => (
              <div key={treatment.id} className="p-6 bg-card-hover transition-theme">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-4 mb-2">
                      <div className="flex items-center gap-2 text-sm text-secondary">
                        <Calendar className="h-4 w-4" />
                        <span>{formatDate(treatment.date)}</span>
                      </div>

                      {treatment.znt && treatment.znt >= 10 && (
                        <span className="inline-flex items-center gap-1 px-2 py-1 bg-warning text-warning text-xs rounded-full">
                          <AlertTriangle className="h-3 w-3" />
                          ZNT {treatment.znt}m
                        </span>
                      )}
                    </div>

                    <div className="flex items-center gap-2 mb-2">
                      <MapPin className="h-4 w-4 text-muted" />
                      <span className="font-medium text-primary">{treatment.parcelle}</span>
                      <span className="text-muted">•</span>
                      <span className="text-secondary">{treatment.culture}</span>
                    </div>

                    <div className="mb-3">
                      <div className="flex items-center gap-2 mb-1">
                        <Beaker className="h-4 w-4 text-blue-600" />
                        <span className="font-medium text-primary">{treatment.produit}</span>
                        <span className="text-sm text-secondary">AMM: {treatment.amm}</span>
                        <button className="text-blue-600 hover:text-blue-800">
                          <ExternalLink className="h-3 w-3" />
                        </button>
                      </div>
                      <div className="text-sm text-secondary">
                        Dose: {treatment.dose} {treatment.unite} • Surface: {treatment.surface} ha •
                        Volume bouillie: {treatment.volume_bouillie} L/ha
                      </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm text-secondary mb-2">
                      <div>
                        <span className="font-medium">Opérateur:</span> {treatment.operateur}
                      </div>
                      <div>
                        <span className="font-medium">Météo:</span> {treatment.conditions_meteo}
                      </div>
                      {treatment.znt && (
                        <div>
                          <span className="font-medium">ZNT:</span>
                          <span className={`ml-1 ${getZntColor(treatment.znt)}`}>
                            {treatment.znt} mètres
                          </span>
                        </div>
                      )}
                    </div>

                    {(treatment.delai_reentree || treatment.delai_recolte) && (
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm mb-2">
                        {treatment.delai_reentree && (
                          <div className={`${isDelayRespected(treatment.date, treatment.delai_reentree) ? 'text-success' : 'text-error'}`}>
                            <span className="font-medium">Délai de rentrée:</span> {treatment.delai_reentree}h
                            {!isDelayRespected(treatment.date, treatment.delai_reentree / 24) && (
                              <span className="ml-1">(en cours)</span>
                            )}
                          </div>
                        )}
                        {treatment.delai_recolte && (
                          <div className={`${isDelayRespected(treatment.date, treatment.delai_recolte) ? 'text-success' : 'text-warning'}`}>
                            <span className="font-medium">Délai avant récolte:</span> {treatment.delai_recolte} jours
                            {!isDelayRespected(treatment.date, treatment.delai_recolte) && (
                              <span className="ml-1">(en cours)</span>
                            )}
                          </div>
                        )}
                      </div>
                    )}

                    {treatment.notes && (
                      <div className="text-sm text-secondary">
                        <span className="font-medium">Notes:</span> {treatment.notes}
                      </div>
                    )}
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

export default Treatments
