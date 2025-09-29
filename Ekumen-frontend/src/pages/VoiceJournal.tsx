import React, { useState, useEffect } from 'react'
import { Calendar, MapPin, Clock, Mic, Save, Edit, Trash2, Plus } from 'lucide-react'
import VoiceInterface from '../components/VoiceInterface'

interface JournalEntry {
  id: string
  date: Date
  parcelle: string
  intervention: string
  description: string
  duration?: number
  weather?: string
  notes?: string
  isVoiceRecorded: boolean
}

const VoiceJournal: React.FC = () => {
  const [entries, setEntries] = useState<JournalEntry[]>([])
  const [showVoiceInterface, setShowVoiceInterface] = useState(false)
  const [editingEntry, setEditingEntry] = useState<string | null>(null)
  const [newEntry, setNewEntry] = useState<Partial<JournalEntry>>({
    date: new Date(),
    parcelle: '',
    intervention: '',
    description: '',
    isVoiceRecorded: false
  })

  // Mock data for demonstration
  useEffect(() => {
    const mockEntries: JournalEntry[] = [
      {
        id: '1',
        date: new Date('2024-01-15'),
        parcelle: 'Parcelle Nord 12ha',
        intervention: 'Traitement fongicide',
        description: 'Application de fongicide contre la septoriose sur blé. Conditions météo favorables, vent faible.',
        duration: 120,
        weather: 'Ensoleillé, 18°C, vent 5 km/h',
        notes: 'Bonne couverture, pas de dérive observée',
        isVoiceRecorded: true
      },
      {
        id: '2',
        date: new Date('2024-01-14'),
        parcelle: 'Parcelle Sud 8ha',
        intervention: 'Semis colza',
        description: 'Semis de colza variété ES Alicia. Préparation du sol effectuée la veille.',
        duration: 90,
        weather: 'Nuageux, 15°C',
        notes: 'Sol en bonnes conditions, levée attendue dans 7-10 jours',
        isVoiceRecorded: false
      }
    ]
    setEntries(mockEntries)
  }, [])

  const handleVoiceMessage = (message: string) => {
    // Parse voice message and create journal entry
    setNewEntry(prev => ({
      ...prev,
      description: message,
      isVoiceRecorded: true
    }))
    setShowVoiceInterface(false)
  }

  const saveEntry = () => {
    if (newEntry.parcelle && newEntry.intervention && newEntry.description) {
      const entry: JournalEntry = {
        id: Date.now().toString(),
        date: newEntry.date || new Date(),
        parcelle: newEntry.parcelle,
        intervention: newEntry.intervention,
        description: newEntry.description,
        duration: newEntry.duration,
        weather: newEntry.weather,
        notes: newEntry.notes,
        isVoiceRecorded: newEntry.isVoiceRecorded || false
      }

      setEntries(prev => [entry, ...prev])
      setNewEntry({
        date: new Date(),
        parcelle: '',
        intervention: '',
        description: '',
        isVoiceRecorded: false
      })
    }
  }

  const deleteEntry = (id: string) => {
    setEntries(prev => prev.filter(entry => entry.id !== id))
  }

  const formatDate = (date: Date) => {
    return date.toLocaleDateString('fr-FR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric'
    })
  }

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString('fr-FR', {
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  return (
    <div className="space-y-6 p-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Journal d'Interventions</h1>
        <p className="mt-1 text-sm text-gray-600">
          Enregistrez vos interventions directement sur le terrain
        </p>
      </div>

      {/* Quick Voice Recording */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">Nouvelle Intervention</h2>
          <button
            onClick={() => setShowVoiceInterface(true)}
            className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
          >
            <Mic className="h-4 w-4" />
            Enregistrement vocal
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Parcelle
            </label>
            <input
              type="text"
              value={newEntry.parcelle || ''}
              onChange={(e) => setNewEntry(prev => ({ ...prev, parcelle: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-green-500 focus:border-green-500"
              placeholder="Ex: Parcelle Nord 12ha"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Type d'intervention
            </label>
            <select
              value={newEntry.intervention || ''}
              onChange={(e) => setNewEntry(prev => ({ ...prev, intervention: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-green-500 focus:border-green-500"
            >
              <option value="">Sélectionner...</option>
              <option value="Traitement fongicide">Traitement fongicide</option>
              <option value="Traitement insecticide">Traitement insecticide</option>
              <option value="Traitement herbicide">Traitement herbicide</option>
              <option value="Fertilisation">Fertilisation</option>
              <option value="Semis">Semis</option>
              <option value="Récolte">Récolte</option>
              <option value="Travail du sol">Travail du sol</option>
              <option value="Autre">Autre</option>
            </select>
          </div>

          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Description
            </label>
            <textarea
              value={newEntry.description || ''}
              onChange={(e) => setNewEntry(prev => ({ ...prev, description: e.target.value }))}
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-green-500 focus:border-green-500"
              placeholder="Décrivez l'intervention effectuée..."
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Durée (minutes)
            </label>
            <input
              type="number"
              value={newEntry.duration || ''}
              onChange={(e) => setNewEntry(prev => ({ ...prev, duration: parseInt(e.target.value) || undefined }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-green-500 focus:border-green-500"
              placeholder="120"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Conditions météo
            </label>
            <input
              type="text"
              value={newEntry.weather || ''}
              onChange={(e) => setNewEntry(prev => ({ ...prev, weather: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-green-500 focus:border-green-500"
              placeholder="Ex: Ensoleillé, 18°C, vent 5 km/h"
            />
          </div>
        </div>

        <div className="mt-4 flex justify-end">
          <button
            onClick={saveEntry}
            disabled={!newEntry.parcelle || !newEntry.intervention || !newEntry.description}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <Save className="h-4 w-4" />
            Enregistrer
          </button>
        </div>
      </div>
      {/* Journal Entries */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">Historique des Interventions</h2>
        </div>

        <div className="divide-y divide-gray-200">
          {entries.length === 0 ? (
            <div className="p-8 text-center text-gray-500">
              <Calendar className="h-12 w-12 mx-auto mb-4 text-gray-300" />
              <p>Aucune intervention enregistrée</p>
              <p className="text-sm">Commencez par enregistrer votre première intervention</p>
            </div>
          ) : (
            entries.map((entry) => (
              <div key={entry.id} className="p-6 hover:bg-gray-50">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-4 mb-2">
                      <div className="flex items-center gap-2 text-sm text-gray-600">
                        <Calendar className="h-4 w-4" />
                        <span>{formatDate(entry.date)}</span>
                        <Clock className="h-4 w-4 ml-2" />
                        <span>{formatTime(entry.date)}</span>
                      </div>

                      {entry.isVoiceRecorded && (
                        <span className="inline-flex items-center gap-1 px-2 py-1 bg-green-100 text-green-800 text-xs rounded-full">
                          <Mic className="h-3 w-3" />
                          Vocal
                        </span>
                      )}
                    </div>

                    <div className="flex items-center gap-2 mb-2">
                      <MapPin className="h-4 w-4 text-gray-400" />
                      <span className="font-medium text-gray-900">{entry.parcelle}</span>
                      <span className="text-gray-400">•</span>
                      <span className="text-gray-700">{entry.intervention}</span>
                    </div>

                    <p className="text-gray-700 mb-3">{entry.description}</p>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm text-gray-600">
                      {entry.duration && (
                        <div>
                          <span className="font-medium">Durée:</span> {entry.duration} min
                        </div>
                      )}
                      {entry.weather && (
                        <div>
                          <span className="font-medium">Météo:</span> {entry.weather}
                        </div>
                      )}
                      {entry.notes && (
                        <div>
                          <span className="font-medium">Notes:</span> {entry.notes}
                        </div>
                      )}
                    </div>
                  </div>

                  <div className="flex items-center gap-2 ml-4">
                    <button
                      onClick={() => setEditingEntry(entry.id)}
                      className="p-2 text-gray-400 hover:text-gray-600 transition-colors"
                      title="Modifier"
                    >
                      <Edit className="h-4 w-4" />
                    </button>
                    <button
                      onClick={() => deleteEntry(entry.id)}
                      className="p-2 text-gray-400 hover:text-red-600 transition-colors"
                      title="Supprimer"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Voice Interface Modal */}
      {showVoiceInterface && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold">Enregistrement Vocal</h3>
              <button
                onClick={() => setShowVoiceInterface(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <div className="mb-4">
              <p className="text-sm text-gray-600">
                Décrivez votre intervention : parcelle, type de traitement, conditions, observations...
              </p>
            </div>

            <VoiceInterface
              onVoiceMessage={handleVoiceMessage}
              className="py-4"
            />
          </div>
        </div>
      )}
    </div>
  )
}

export default VoiceJournal
