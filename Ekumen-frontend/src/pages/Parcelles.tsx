import React, { useState, useEffect } from 'react'
import { MapPin, Crop, Calendar, BarChart3, Eye, Edit, Plus, Search } from 'lucide-react'

interface Parcelle {
  id: string
  nom: string
  surface: number
  culture_actuelle: string
  variete?: string
  date_semis?: Date
  date_recolte_prevue?: Date
  rendement_prevu?: number
  rendement_realise?: number
  coordonnees?: {
    latitude: number
    longitude: number
  }
  sol_type?: string
  irrigation?: boolean
  derniere_intervention?: Date
  statut: 'seme' | 'en_croissance' | 'recolte' | 'jachère'
  notes?: string
}

const Parcelles: React.FC = () => {
  const [parcelles, setParcelles] = useState<Parcelle[]>([])
  const [filteredParcelles, setFilteredParcelles] = useState<Parcelle[]>([])
  const [searchTerm, setSearchTerm] = useState('')
  const [filterCulture, setFilterCulture] = useState<string>('all')
  const [filterStatut, setFilterStatut] = useState<string>('all')
  const [showAddModal, setShowAddModal] = useState(false)

  // Mock data from MesParcelles
  useEffect(() => {
    const mockParcelles: Parcelle[] = [
      {
        id: '1',
        nom: 'Parcelle Nord',
        surface: 12.5,
        culture_actuelle: 'Blé tendre',
        variete: 'Apache',
        date_semis: new Date('2023-10-15'),
        date_recolte_prevue: new Date('2024-07-20'),
        rendement_prevu: 75,
        coordonnees: { latitude: 48.8566, longitude: 2.3522 },
        sol_type: 'Limon argileux',
        irrigation: false,
        derniere_intervention: new Date('2024-01-15'),
        statut: 'en_croissance',
        notes: 'Parcelle en pente douce, exposition sud'
      },
      {
        id: '2',
        nom: 'Parcelle Sud',
        surface: 8.2,
        culture_actuelle: 'Colza',
        variete: 'ES Alicia',
        date_semis: new Date('2023-08-25'),
        date_recolte_prevue: new Date('2024-07-10'),
        rendement_prevu: 35,
        coordonnees: { latitude: 48.8556, longitude: 2.3512 },
        sol_type: 'Argilo-calcaire',
        irrigation: false,
        derniere_intervention: new Date('2024-01-10'),
        statut: 'en_croissance',
        notes: 'Bonne exposition, drainage naturel'
      },
      {
        id: '3',
        nom: 'Parcelle Est',
        surface: 15.0,
        culture_actuelle: 'Orge',
        variete: 'KWS Cassia',
        date_semis: new Date('2023-10-20'),
        date_recolte_prevue: new Date('2024-07-15'),
        rendement_prevu: 68,
        coordonnees: { latitude: 48.8576, longitude: 2.3532 },
        sol_type: 'Limon sableux',
        irrigation: true,
        derniere_intervention: new Date('2024-01-08'),
        statut: 'en_croissance'
      },
      {
        id: '4',
        nom: 'Parcelle Ouest',
        surface: 10.8,
        culture_actuelle: 'Blé tendre',
        variete: 'Rubisko',
        date_semis: new Date('2023-10-12'),
        date_recolte_prevue: new Date('2024-07-25'),
        rendement_prevu: 72,
        coordonnees: { latitude: 48.8546, longitude: 2.3502 },
        sol_type: 'Argilo-limoneux',
        irrigation: false,
        derniere_intervention: new Date('2024-01-13'),
        statut: 'en_croissance'
      },
      {
        id: '5',
        nom: 'Parcelle Centre',
        surface: 6.5,
        culture_actuelle: 'Jachère',
        date_recolte_prevue: new Date('2024-08-01'),
        coordonnees: { latitude: 48.8536, longitude: 2.3492 },
        sol_type: 'Sablo-limoneux',
        irrigation: false,
        statut: 'jachère',
        notes: 'En jachère pour rotation, semis tournesol prévu'
      }
    ]
    setParcelles(mockParcelles)
    setFilteredParcelles(mockParcelles)
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

  const formatDate = (date: Date) => {
    return date.toLocaleDateString('fr-FR', {
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
          <h1 className="text-2xl font-bold text-gray-900">Gestion des Parcelles</h1>
          <p className="mt-1 text-sm text-gray-600">
            Vue d'ensemble de vos parcelles et cultures
          </p>
        </div>
        <button
          onClick={() => setShowAddModal(true)}
          className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
        >
          <Plus className="h-4 w-4" />
          Nouvelle parcelle
        </button>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-lg shadow p-4">
          <div className="text-2xl font-bold text-gray-900">{filteredParcelles.length}</div>
          <div className="text-sm text-gray-600">Parcelles</div>
        </div>
        <div className="bg-white rounded-lg shadow p-4">
          <div className="text-2xl font-bold text-green-600">{totalSurface.toFixed(1)} ha</div>
          <div className="text-sm text-gray-600">Surface totale</div>
        </div>
        <div className="bg-white rounded-lg shadow p-4">
          <div className="text-2xl font-bold text-blue-600">{rendementMoyen.toFixed(1)} q/ha</div>
          <div className="text-sm text-gray-600">Rendement moyen prévu</div>
        </div>
        <div className="bg-white rounded-lg shadow p-4">
          <div className="text-2xl font-bold text-yellow-600">
            {filteredParcelles.filter(p => p.irrigation).length}
          </div>
          <div className="text-sm text-gray-600">Avec irrigation</div>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow p-4">
        <div className="flex flex-col md:flex-row gap-4">
          {/* Search */}
          <div className="flex-1">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
              <input
                type="text"
                placeholder="Rechercher par nom, culture, variété..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:ring-green-500 focus:border-green-500"
              />
            </div>
          </div>

          {/* Culture Filter */}
          <div>
            <select
              value={filterCulture}
              onChange={(e) => setFilterCulture(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-md focus:ring-green-500 focus:border-green-500"
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
              className="px-3 py-2 border border-gray-300 rounded-md focus:ring-green-500 focus:border-green-500"
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

      {/* Parcelles Table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        {filteredParcelles.length === 0 ? (
          <div className="p-8 text-center text-gray-500">
            <MapPin className="h-12 w-12 mx-auto mb-4 text-gray-300" />
            <p>Aucune parcelle trouvée</p>
            <p className="text-sm">Modifiez vos filtres ou ajoutez une nouvelle parcelle</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Parcelle
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Culture
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Surface
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Statut
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Rendement prévu
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Sol / Irrigation
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Dates importantes
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
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
