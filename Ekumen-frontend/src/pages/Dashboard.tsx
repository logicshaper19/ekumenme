import React from 'react'
import { Wheat, MessageCircle, Package, BarChart3, Calendar, MapPin, User, CheckCircle, AlertTriangle, Clock, Search } from 'lucide-react'

// Components
import { AgriculturalCard } from '@components/AgriculturalCard'
import { Button } from '@components/ui/Button'

// Hooks
import { useAuth } from '@hooks/useAuth'

const Dashboard: React.FC = () => {
  const { user } = useAuth()
  
  // Sample interventions data - in real app, this would come from API
  const latestInterventions = [
    {
      id: 1,
      type: 'Traitement phytosanitaire',
      parcel: 'Parcelle A1 - Blé d\'hiver',
      date: '2024-01-15',
      time: '14:30',
      operator: 'Jean Dupont',
      status: 'completed',
      product: 'Fongicide Pro',
      dose: '2.5 L/ha'
    },
    {
      id: 2,
      type: 'Fertilisation',
      parcel: 'Parcelle B2 - Colza',
      date: '2024-01-14',
      time: '09:15',
      operator: 'Marie Martin',
      status: 'completed',
      product: 'Engrais NPK 15-15-15',
      dose: '300 kg/ha'
    },
    {
      id: 3,
      type: 'Semis',
      parcel: 'Parcelle C3 - Maïs',
      date: '2024-01-13',
      time: '16:45',
      operator: 'Pierre Durand',
      status: 'pending',
      product: 'Semences Maïs Pioneer',
      dose: '80 000 grains/ha'
    },
    {
      id: 4,
      type: 'Désherbage',
      parcel: 'Parcelle A2 - Blé d\'hiver',
      date: '2024-01-12',
      time: '11:20',
      operator: 'Sophie Leroy',
      status: 'completed',
      product: 'Herbicide Sélectif',
      dose: '1.8 L/ha'
    },
    {
      id: 5,
      type: 'Irrigation',
      parcel: 'Parcelle D1 - Légumes',
      date: '2024-01-11',
      time: '08:00',
      operator: 'Marc Petit',
      status: 'in_progress',
      product: 'Eau d\'irrigation',
      dose: '25 mm'
    }
  ]

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="h-4 w-4 text-success-600" />
      case 'pending':
        return <Clock className="h-4 w-4 text-warning-600" />
      case 'in_progress':
        return <AlertTriangle className="h-4 w-4 text-gray-600" />
      default:
        return <Clock className="h-4 w-4 text-gray-400" />
    }
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'completed':
        return <span className="badge-agricultural-success">Terminé</span>
      case 'pending':
        return <span className="badge-agricultural-warning">En attente</span>
      case 'in_progress':
        return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">En cours</span>
      default:
        return <span className="badge-agricultural-error">Inconnu</span>
    }
  }

  const stats = [
    {
      title: 'Parcelles Actives',
      value: '12',
      unit: 'ha',
      change: '+2',
      changeType: 'positive' as const,
      icon: Wheat
    },
    {
      title: 'Interventions Ce Mois',
      value: '8',
      unit: 'traitements',
      change: '+3',
      changeType: 'positive' as const,
      icon: MessageCircle
    },
    {
      title: 'Produits Utilisés',
      value: '15',
      unit: 'produits',
      change: '+2',
      changeType: 'positive' as const,
      icon: Package
    },
    {
      title: 'Rendement Moyen',
      value: '85',
      unit: 'q/ha',
      change: '+12%',
      changeType: 'positive' as const,
      icon: BarChart3
    }
  ]

  return (
    <div className="space-y-2">
      {/* Header */}
      <div>
        <h1 className="text-xl font-bold text-gray-900">Tableau de Bord</h1>
        <p className="mt-1 text-xs text-gray-600">
          {user?.role === 'farmer' 
            ? 'Vue d\'ensemble de votre exploitation agricole'
            : user?.role === 'advisor'
            ? 'Vue d\'ensemble des exploitations suivies'
            : user?.role === 'inspector'
            ? 'Vue d\'ensemble des contrôles et inspections'
            : 'Vue d\'ensemble du système agricole'
          }
        </p>
      </div>

      {/* Stats Grid - Using Data Display Components */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-2">
        {stats.map((stat, index) => {
          const Icon = stat.icon
          return (
            <AgriculturalCard
              key={stat.title}
                type="farm-data"
                status="info"
                className="h-full"
                showAccent={false}
              >
                <div className="p-4">
                  <div className="flex items-center justify-between mb-3">
                    <div className="text-sm font-medium text-gray-600">{stat.title}</div>
                    <div className="w-8 h-8 bg-gray-100 rounded-lg flex items-center justify-center">
                      <Icon className="h-4 w-4 text-gray-600" />
                    </div>
                  </div>
                  <div className="flex items-baseline mb-1">
                    <div className="text-2xl font-bold text-gray-900">{stat.value}</div>
                    <div className="text-sm text-gray-500 ml-1">{stat.unit}</div>
                  </div>
                  <div className={`text-sm font-medium ${
                    stat.changeType === 'positive' ? 'text-green-600' : 'text-red-600'
                  }`}>
                    {stat.change} ce mois
                  </div>
                </div>
              </AgriculturalCard>
          )
        })}
      </div>

      {/* Search Bar - Right Aligned */}
      <div className="flex justify-end py-4">
        <div className="flex items-center space-x-3">
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <Search className="h-4 w-4 text-gray-400" />
            </div>
            <input
              type="text"
              placeholder="Rechercher dans les interventions..."
              className="block w-64 pl-10 pr-3 py-2 border border-gray-300 rounded-lg text-sm placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            />
          </div>
          <div className="relative">
            <Button variant="outline" size="sm" className="flex items-center space-x-2">
              <span>Filtrer</span>
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </Button>
            {/* Filter Dropdown - Hidden by default, would be shown on click */}
            <div className="absolute right-0 mt-2 w-56 bg-white rounded-lg shadow-lg border border-gray-200 hidden">
              <div className="p-4 space-y-3">
                <div>
                  <label className="block text-xs font-medium text-gray-700 mb-1">Statut</label>
                  <select className="w-full px-3 py-1 border border-gray-300 rounded text-sm focus:outline-none focus:ring-1 focus:ring-primary-500">
                    <option>Tous les statuts</option>
                    <option>Terminé</option>
                    <option>En cours</option>
                    <option>En attente</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-700 mb-1">Type d'intervention</label>
                  <select className="w-full px-3 py-1 border border-gray-300 rounded text-sm focus:outline-none focus:ring-1 focus:ring-primary-500">
                    <option>Tous les types</option>
                    <option>Traitement phytosanitaire</option>
                    <option>Fertilisation</option>
                    <option>Semis</option>
                    <option>Désherbage</option>
                    <option>Irrigation</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-700 mb-1">Période</label>
                  <select className="w-full px-3 py-1 border border-gray-300 rounded text-sm focus:outline-none focus:ring-1 focus:ring-primary-500">
                    <option>Dernière semaine</option>
                    <option>Dernier mois</option>
                    <option>Derniers 3 mois</option>
                    <option>Tout</option>
                  </select>
                </div>
                <div className="flex justify-end space-x-2 pt-2 border-t border-gray-200">
                  <Button variant="ghost" size="sm">Réinitialiser</Button>
                  <Button variant="primary" size="sm">Appliquer</Button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Latest Interventions Table */}
      <AgriculturalCard
        type="planning"
        status="info"
        title="Dernières Interventions"
        subtitle={`Dernière mise à jour: ${new Date().toLocaleString('fr-FR')}`}
        showAccent={false}
      >
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-3 py-2 text-left text-xs font-semibold text-gray-900 uppercase tracking-wider">
                  Type d'Intervention
                </th>
                <th className="px-3 py-2 text-left text-xs font-semibold text-gray-900 uppercase tracking-wider">
                  Parcelle
                </th>
                <th className="px-3 py-2 text-left text-xs font-semibold text-gray-900 uppercase tracking-wider">
                  Date & Heure
                </th>
                <th className="px-3 py-2 text-left text-xs font-semibold text-gray-900 uppercase tracking-wider">
                  Opérateur
                </th>
                <th className="px-3 py-2 text-left text-xs font-semibold text-gray-900 uppercase tracking-wider">
                  Produit/Dose
                </th>
                <th className="px-3 py-2 text-left text-xs font-semibold text-gray-900 uppercase tracking-wider">
                  Statut
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {latestInterventions.map((intervention) => (
                <tr key={intervention.id} className="hover:bg-gray-50 transition-colors duration-150">
                  <td className="px-3 py-2 whitespace-nowrap">
                    <div className="flex items-center">
                      {getStatusIcon(intervention.status)}
                      <div className="ml-3">
                        <div className="text-xs font-semibold text-gray-900">
                          {intervention.type}
                        </div>
                      </div>
                    </div>
                  </td>
                  <td className="px-3 py-2 whitespace-nowrap">
                    <div className="flex items-center text-xs text-gray-900">
                      <MapPin className="h-4 w-4 text-gray-400 mr-2" />
                      {intervention.parcel}
                    </div>
                  </td>
                  <td className="px-3 py-2 whitespace-nowrap">
                    <div className="flex items-center text-xs text-gray-900">
                      <Calendar className="h-4 w-4 text-gray-400 mr-2" />
                      <div>
                        <div className="font-medium">{new Date(intervention.date).toLocaleDateString('fr-FR')}</div>
                        <div className="text-xs text-gray-500">{intervention.time}</div>
                      </div>
                    </div>
                  </td>
                  <td className="px-3 py-2 whitespace-nowrap">
                    <div className="flex items-center text-xs text-gray-900">
                      <User className="h-4 w-4 text-gray-400 mr-2" />
                      {intervention.operator}
                    </div>
                  </td>
                  <td className="px-6 py-5 whitespace-nowrap text-sm text-gray-900">
                    <div>
                      <div className="font-semibold">{intervention.product}</div>
                      <div className="text-xs text-gray-500">{intervention.dose}</div>
                    </div>
                  </td>
                  <td className="px-3 py-2 whitespace-nowrap">
                    {getStatusBadge(intervention.status)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        
        {/* View All Button */}
        <div className="mt-4 flex justify-end border-t border-gray-200 pt-3">
          <Button variant="outline" size="sm">
            Voir toutes les interventions
          </Button>
        </div>
      </AgriculturalCard>
    </div>
  )
}

export default Dashboard
