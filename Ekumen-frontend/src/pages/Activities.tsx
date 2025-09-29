import React, { useState, useEffect } from 'react'
import { Calendar, MapPin, Clock, Filter, Search, Download, Eye } from 'lucide-react'

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

  // Mock data from MesParcelles
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
        <h1 className="text-2xl font-bold text-gray-900">Activités Agricoles</h1>
        <p className="mt-1 text-sm text-gray-600">
          Historique des interventions et activités sur vos parcelles
        </p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-lg shadow p-4">
          <div className="text-2xl font-bold text-gray-900">{filteredActivities.length}</div>
          <div className="text-sm text-gray-600">Activités</div>
        </div>
        <div className="bg-white rounded-lg shadow p-4">
          <div className="text-2xl font-bold text-green-600">{totalSurface.toFixed(1)} ha</div>
          <div className="text-sm text-gray-600">Surface totale</div>
        </div>
        <div className="bg-white rounded-lg shadow p-4">
          <div className="text-2xl font-bold text-blue-600">{formatCurrency(totalCost)}</div>
          <div className="text-sm text-gray-600">Coût total</div>
        </div>
        <div className="bg-white rounded-lg shadow p-4">
          <div className="text-2xl font-bold text-yellow-600">
            {filteredActivities.filter(a => a.statut === 'planifie').length}
          </div>
          <div className="text-sm text-gray-600">Planifiées</div>
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
                placeholder="Rechercher par parcelle, culture, intervention..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:ring-green-500 focus:border-green-500"
              />
            </div>
          </div>

          {/* Status Filter */}
          <div>
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-md focus:ring-green-500 focus:border-green-500"
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
            Exporter
          </button>
        </div>
      </div>

      {/* Activities List */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">Liste des Activités</h2>
        </div>

        <div className="divide-y divide-gray-200">
          {filteredActivities.length === 0 ? (
            <div className="p-8 text-center text-gray-500">
              <Calendar className="h-12 w-12 mx-auto mb-4 text-gray-300" />
              <p>Aucune activité trouvée</p>
              <p className="text-sm">Modifiez vos filtres pour voir plus d'activités</p>
            </div>
          ) : (
            filteredActivities.map((activity) => (
              <div key={activity.id} className="p-6 hover:bg-gray-50">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-4 mb-2">
                      <div className="flex items-center gap-2 text-sm text-gray-600">
                        <Calendar className="h-4 w-4" />
                        <span>{formatDate(activity.date)}</span>
                      </div>
                      
                      <span className={`inline-flex items-center px-2 py-1 text-xs rounded-full ${getStatusColor(activity.statut)}`}>
                        {getStatusText(activity.statut)}
                      </span>
                    </div>

                    <div className="flex items-center gap-2 mb-2">
                      <MapPin className="h-4 w-4 text-gray-400" />
                      <span className="font-medium text-gray-900">{activity.parcelle}</span>
                      <span className="text-gray-400">•</span>
                      <span className="text-gray-700">{activity.culture}</span>
                      <span className="text-gray-400">•</span>
                      <span className="text-gray-700">{activity.intervention}</span>
                    </div>

                    {activity.produits && activity.produits.length > 0 && (
                      <div className="mb-2">
                        <span className="text-sm text-gray-600">Produits: </span>
                        <span className="text-sm text-gray-900">{activity.produits.join(', ')}</span>
                      </div>
                    )}

                    <div className="grid grid-cols-1 md:grid-cols-4 gap-4 text-sm text-gray-600">
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

export default Activities
