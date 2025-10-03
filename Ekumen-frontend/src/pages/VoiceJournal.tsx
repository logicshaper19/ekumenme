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
        <h1 className="text-2xl font-bold text-primary">Journal d'Interventions</h1>
        <p className="mt-1 text-sm text-secondary">
          Enregistrez vos interventions directement sur le terrain
        </p>
      </div>

      {/* Quick Voice Recording */}
      <div className="card p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-primary">Nouvelle Intervention</h2>
          <button
            onClick={() => setShowVoiceInterface(true)}
            className="btn-primary"
          >
            <Mic className="h-4 w-4" />
            Enregistrement vocal
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-primary mb-1">
              Parcelle
            </label>
            <input
              type="text"
              value={newEntry.parcelle || ''}
              onChange={(e) => setNewEntry(prev => ({ ...prev, parcelle: e.target.value }))}
              className="input"
              placeholder="Ex: Parcelle Nord 12ha"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-primary mb-1">
              Type d'intervention
            </label>
            <select
              value={newEntry.intervention || ''}
              onChange={(e) => setNewEntry(prev => ({ ...prev, intervention: e.target.value }))}
              className="input"
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
            <label className="block text-sm font-medium text-primary mb-1">
              Description
            </label>
            <textarea
              value={newEntry.description || ''}
              onChange={(e) => setNewEntry(prev => ({ ...prev, description: e.target.value }))}
              rows={3}
              className="input"
              placeholder="Décrivez l'intervention effectuée..."
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-primary mb-1">
              Durée (minutes)
            </label>
            <input
              type="number"
              value={newEntry.duration || ''}
              onChange={(e) => setNewEntry(prev => ({ ...prev, duration: parseInt(e.target.value) || undefined }))}
              className="input"
              placeholder="120"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-primary mb-1">
              Conditions météo
            </label>
            <input
              type="text"
              value={newEntry.weather || ''}
              onChange={(e) => setNewEntry(prev => ({ ...prev, weather: e.target.value }))}
              className="input"
              placeholder="Ex: Ensoleillé, 18°C, vent 5 km/h"
            />
          </div>
        </div>

        <div className="mt-4 flex justify-end">
          <button
            onClick={saveEntry}
            disabled={!newEntry.parcelle || !newEntry.intervention || !newEntry.description}
            className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Save className="h-4 w-4" />
            Enregistrer
          </button>
        </div>
      </div>
      {/* Journal Entries */}
      <div className="card">
        <div className="px-6 py-4 border-b border-subtle">
          <h2 className="text-lg font-semibold text-primary">Historique des Interventions</h2>
        </div>

        <div className="divide-y divide-subtle">
          {entries.length === 0 ? (
            <div className="p-8 text-center text-muted">
              <Calendar className="h-12 w-12 mx-auto mb-4 text-muted" />
              <p>Aucune intervention enregistrée</p>
              <p className="text-sm">Commencez par enregistrer votre première intervention</p>
            </div>
          ) : (
            entries.map((entry) => (
              <div key={entry.id} className="p-6 bg-card-hover transition-theme">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-4 mb-2">
                      <div className="flex items-center gap-2 text-sm text-secondary">
                        <Calendar className="h-4 w-4" />
                        <span>{formatDate(entry.date)}</span>
                        <Clock className="h-4 w-4 ml-2" />
                        <span>{formatTime(entry.date)}</span>
                      </div>

                      {entry.isVoiceRecorded && (
                        <span className="inline-flex items-center gap-1 px-2 py-1 bg-success text-success text-xs rounded-full">
                          <Mic className="h-3 w-3" />
                          Vocal
                        </span>
                      )}
                    </div>

                    <div className="flex items-center gap-2 mb-2">
                      <MapPin className="h-4 w-4 text-muted" />
                      <span className="font-medium text-primary">{entry.parcelle}</span>
                      <span className="text-muted">•</span>
                      <span className="text-secondary">{entry.intervention}</span>
                    </div>

                    <p className="text-secondary mb-3">{entry.description}</p>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm text-secondary">
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
                      className="p-2 text-muted hover:text-primary transition-theme"
                      title="Modifier"
                    >
                      <Edit className="h-4 w-4" />
                    </button>
                    <button
                      onClick={() => deleteEntry(entry.id)}
                      className="p-2 text-muted hover:text-error transition-theme"
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
          <div className="bg-elevated rounded-lg p-6 max-w-md w-full mx-4">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold text-primary">Enregistrement Vocal</h3>
              <button
                onClick={() => setShowVoiceInterface(false)}
                className="text-muted hover:text-primary transition-theme"
              >
                <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <div className="mb-4">
              <p className="text-sm text-secondary">
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
