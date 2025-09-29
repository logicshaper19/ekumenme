import React, { useState, useEffect } from 'react'
import { Beaker, Calendar, MapPin, AlertTriangle, Search, Filter, Download, Eye, ExternalLink } from 'lucide-react'

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

  // Mock data from EPHY database
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
        <h1 className="text-2xl font-bold text-gray-900">Traitements Phytosanitaires</h1>
        <p className="mt-1 text-sm text-gray-600">
          Historique des produits phytosanitaires utilisés sur vos parcelles
        </p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-lg shadow p-4">
          <div className="text-2xl font-bold text-gray-900">{filteredTreatments.length}</div>
          <div className="text-sm text-gray-600">Traitements</div>
        </div>
        <div className="bg-white rounded-lg shadow p-4">
          <div className="text-2xl font-bold text-green-600">{totalSurface.toFixed(1)} ha</div>
          <div className="text-sm text-gray-600">Surface traitée</div>
        </div>
        <div className="bg-white rounded-lg shadow p-4">
          <div className="text-2xl font-bold text-blue-600">{totalVolume.toFixed(2)} L</div>
          <div className="text-sm text-gray-600">Volume total</div>
        </div>
        <div className="bg-white rounded-lg shadow p-4">
          <div className="text-2xl font-bold text-yellow-600">
            {new Set(filteredTreatments.map(t => t.produit)).size}
          </div>
          <div className="text-sm text-gray-600">Produits différents</div>
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
                placeholder="Rechercher par produit, AMM, parcelle..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:ring-green-500 focus:border-green-500"
              />
            </div>
          </div>

          {/* Parcelle Filter */}
          <div>
            <select
              value={filterParcelle}
              onChange={(e) => setFilterParcelle(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-md focus:ring-green-500 focus:border-green-500"
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
              className="px-3 py-2 border border-gray-300 rounded-md focus:ring-green-500 focus:border-green-500"
            >
              <option value="all">Toute la période</option>
              <option value="week">7 derniers jours</option>
              <option value="month">30 derniers jours</option>
            </select>
          </div>

          {/* Export Button */}
          <button className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors">
            <Download className="h-4 w-4" />
            Registre
          </button>
        </div>
      </div>

      {/* Treatments List */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">Registre des Traitements</h2>
        </div>

        <div className="divide-y divide-gray-200">
          {filteredTreatments.length === 0 ? (
            <div className="p-8 text-center text-gray-500">
              <Beaker className="h-12 w-12 mx-auto mb-4 text-gray-300" />
              <p>Aucun traitement trouvé</p>
              <p className="text-sm">Modifiez vos filtres pour voir plus de traitements</p>
            </div>
          ) : (
            filteredTreatments.map((treatment) => (
              <div key={treatment.id} className="p-6 hover:bg-gray-50">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-4 mb-2">
                      <div className="flex items-center gap-2 text-sm text-gray-600">
                        <Calendar className="h-4 w-4" />
                        <span>{formatDate(treatment.date)}</span>
                      </div>
                      
                      {treatment.znt && treatment.znt >= 10 && (
                        <span className="inline-flex items-center gap-1 px-2 py-1 bg-yellow-100 text-yellow-800 text-xs rounded-full">
                          <AlertTriangle className="h-3 w-3" />
                          ZNT {treatment.znt}m
                        </span>
                      )}
                    </div>

                    <div className="flex items-center gap-2 mb-2">
                      <MapPin className="h-4 w-4 text-gray-400" />
                      <span className="font-medium text-gray-900">{treatment.parcelle}</span>
                      <span className="text-gray-400">•</span>
                      <span className="text-gray-700">{treatment.culture}</span>
                    </div>

                    <div className="mb-3">
                      <div className="flex items-center gap-2 mb-1">
                        <Beaker className="h-4 w-4 text-blue-600" />
                        <span className="font-medium text-gray-900">{treatment.produit}</span>
                        <span className="text-sm text-gray-600">AMM: {treatment.amm}</span>
                        <button className="text-blue-600 hover:text-blue-800">
                          <ExternalLink className="h-3 w-3" />
                        </button>
                      </div>
                      <div className="text-sm text-gray-700">
                        Dose: {treatment.dose} {treatment.unite} • Surface: {treatment.surface} ha • 
                        Volume bouillie: {treatment.volume_bouillie} L/ha
                      </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm text-gray-600 mb-2">
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
                          <div className={`${isDelayRespected(treatment.date, treatment.delai_reentree) ? 'text-green-600' : 'text-red-600'}`}>
                            <span className="font-medium">Délai de rentrée:</span> {treatment.delai_reentree}h
                            {!isDelayRespected(treatment.date, treatment.delai_reentree / 24) && (
                              <span className="ml-1">(en cours)</span>
                            )}
                          </div>
                        )}
                        {treatment.delai_recolte && (
                          <div className={`${isDelayRespected(treatment.date, treatment.delai_recolte) ? 'text-green-600' : 'text-orange-600'}`}>
                            <span className="font-medium">Délai avant récolte:</span> {treatment.delai_recolte} jours
                            {!isDelayRespected(treatment.date, treatment.delai_recolte) && (
                              <span className="ml-1">(en cours)</span>
                            )}
                          </div>
                        )}
                      </div>
                    )}

                    {treatment.notes && (
                      <div className="text-sm text-gray-700">
                        <span className="font-medium">Notes:</span> {treatment.notes}
                      </div>
                    )}
                  </div>

                  <div className="flex items-center gap-2 ml-4">
                    <button
                      className="p-2 text-gray-400 hover:text-gray-600 transition-colors"
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
    </div>
  )
}

export default Treatments
