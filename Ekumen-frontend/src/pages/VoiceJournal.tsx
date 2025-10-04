import React, { useState, useEffect } from 'react'
import { Calendar, MapPin, Clock, Mic, Save, Edit, Trash2, Plus, BarChart3, TrendingUp, Activity } from 'lucide-react'
import VoiceInterface from '../components/VoiceInterface'
import StreamingVoiceAssistant from '../components/StreamingVoiceAssistant'
import EnhancedVoiceInterface from '../components/EnhancedVoiceInterface'

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
  const [showStreamingVoice, setShowStreamingVoice] = useState(false)
  const [showEnhancedVoice, setShowEnhancedVoice] = useState(false)
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
    const entry: JournalEntry = {
      id: Date.now().toString(),
      date: new Date(),
      parcelle: 'Parcelle (à préciser)', // Default value, can be edited later
      intervention: 'Intervention (à préciser)', // Default value, can be edited later
      description: message,
      isVoiceRecorded: true
    }

    setEntries(prev => [entry, ...prev])
    setShowVoiceInterface(false)
  }

  const handleStreamingJournalEntry = (journalData: any) => {
    // Handle structured journal data from streaming voice assistant
    console.log('Received journal data:', journalData)
    
    // Create journal entry from structured data
    const entry: JournalEntry = {
      id: Date.now().toString(),
      date: new Date(),
      parcelle: journalData.data?.parcelle || 'Parcelle (à préciser)',
      intervention: journalData.data?.intervention_type || 'Intervention (à préciser)',
      description: journalData.data?.content || 'Description générée par IA',
      duration: journalData.data?.duration_minutes,
      weather: journalData.data?.weather_conditions,
      notes: journalData.data?.notes,
      isVoiceRecorded: true
    }

    setEntries(prev => [entry, ...prev])
    setShowStreamingVoice(false)
  }

  const handleEnhancedJournalEntry = (entry: any) => {
    console.log('Received enhanced journal entry:', entry)
    const journalEntry: JournalEntry = {
      id: entry.id,
      date: new Date(entry.created_at),
      parcelle: 'Parcelle (à préciser)',
      intervention: 'Intervention (à préciser)',
      description: entry.transcript,
      notes: `Statut: ${entry.status}`,
      isVoiceRecorded: true
    }
    setEntries(prev => [journalEntry, ...prev])
    setShowEnhancedVoice(false)
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

      {/* Analytics Section */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
        <div className="card p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-secondary">Total Interventions</p>
              <p className="text-2xl font-bold text-primary">{entries.length}</p>
            </div>
            <div className="p-3 bg-primary/10 rounded-lg">
              <Activity className="h-6 w-6 text-primary" />
            </div>
          </div>
          <div className="mt-2">
            <span className="text-sm text-success flex items-center">
              <TrendingUp className="h-4 w-4 mr-1" />
              +12% ce mois
            </span>
          </div>
        </div>

        <div className="card p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-secondary">Temps Total</p>
              <p className="text-2xl font-bold text-primary">
                {Math.round(entries.reduce((acc, entry) => acc + (entry.duration || 0), 0) / 60)}h
              </p>
            </div>
            <div className="p-3 bg-success/10 rounded-lg">
              <Clock className="h-6 w-6 text-success" />
            </div>
          </div>
          <div className="mt-2">
            <span className="text-sm text-secondary">
              Moyenne: {Math.round(entries.reduce((acc, entry) => acc + (entry.duration || 0), 0) / entries.length)} min
            </span>
          </div>
        </div>

        <div className="card p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-secondary">Enregistrements Vocaux</p>
              <p className="text-2xl font-bold text-primary">
                {entries.filter(entry => entry.isVoiceRecorded).length}
              </p>
            </div>
            <div className="p-3 bg-warning/10 rounded-lg">
              <Mic className="h-6 w-6 text-warning" />
            </div>
          </div>
          <div className="mt-2">
            <span className="text-sm text-secondary">
              {Math.round((entries.filter(entry => entry.isVoiceRecorded).length / entries.length) * 100)}% du total
            </span>
          </div>
        </div>
      </div>
      {/* Journal Entries */}
      <div className="card">
        <div className="px-6 py-4 border-b border-subtle flex items-center justify-between">
          <h2 className="text-lg font-semibold text-primary">Historique des Interventions</h2>
          <div className="flex items-center gap-2">
        <button
          onClick={() => setShowEnhancedVoice(true)}
          className="btn-primary flex items-center gap-2"
        >
          <Mic className="h-4 w-4" />
          Assistant Vocal (Nouveau)
        </button>
        <button
          onClick={() => setShowStreamingVoice(true)}
          className="btn-secondary flex items-center gap-2"
        >
          <Mic className="h-4 w-4" />
          Assistant Vocal IA
        </button>
        <button
          onClick={() => setShowVoiceInterface(true)}
          className="btn-secondary flex items-center gap-2"
        >
          <Plus className="h-4 w-4" />
          Ajouter Manuel
        </button>
          </div>
        </div>

        {entries.length === 0 ? (
          <div className="p-8 text-center text-muted">
            <Calendar className="h-12 w-12 mx-auto mb-4 text-muted" />
            <p>Aucune intervention enregistrée</p>
            <p className="text-sm">Commencez par enregistrer votre première intervention</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full divide-y divide-subtle text-xs">
              <thead className="bg-card-hover">
                <tr>
                  <th className="px-3 py-2 text-left text-xs font-medium text-muted uppercase tracking-wider w-32">
                    Date & Heure
                  </th>
                  <th className="px-3 py-2 text-left text-xs font-medium text-muted uppercase tracking-wider w-24">
                    Parcelle
                  </th>
                  <th className="px-3 py-2 text-left text-xs font-medium text-muted uppercase tracking-wider w-28">
                    Intervention
                  </th>
                  <th className="px-3 py-2 text-left text-xs font-medium text-muted uppercase tracking-wider">
                    Description
                  </th>
                  <th className="px-3 py-2 text-left text-xs font-medium text-muted uppercase tracking-wider w-16">
                    Durée
                  </th>
                  <th className="px-3 py-2 text-left text-xs font-medium text-muted uppercase tracking-wider w-20">
                    Météo
                  </th>
                  <th className="px-3 py-2 text-left text-xs font-medium text-muted uppercase tracking-wider w-20">
                    Type
                  </th>
                  <th className="px-3 py-2 text-right text-xs font-medium text-muted uppercase tracking-wider w-20">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-card divide-y divide-subtle">
                {entries.map((entry) => (
                  <tr key={entry.id} className="hover:bg-gray-50">
                    <td className="px-3 py-2 whitespace-nowrap">
                      <div className="flex items-center">
                        <Calendar className="h-3 w-3 text-gray-400 mr-1" />
                        <div>
                          <div className="text-xs font-medium text-gray-900">{formatDate(entry.date)}</div>
                          <div className="text-xs text-gray-500 flex items-center">
                            <Clock className="h-2 w-2 mr-1" />
                            {formatTime(entry.date)}
                          </div>
                        </div>
                      </div>
                    </td>
                    <td className="px-3 py-2 whitespace-nowrap">
                      <div className="flex items-center">
                        <MapPin className="h-3 w-3 text-green-500 mr-1" />
                        <div className="text-xs font-medium text-gray-900 truncate">{entry.parcelle}</div>
                      </div>
                    </td>
                    <td className="px-3 py-2 whitespace-nowrap">
                      <div className="text-xs text-gray-900 truncate">{entry.intervention}</div>
                    </td>
                    <td className="px-3 py-2">
                      <div className="text-xs text-gray-900 max-w-xs truncate" title={entry.description}>
                        {entry.description}
                      </div>
                    </td>
                    <td className="px-3 py-2 whitespace-nowrap">
                      {entry.duration ? (
                        <div className="text-xs text-gray-900">{entry.duration} min</div>
                      ) : (
                        <span className="text-gray-400 text-xs">-</span>
                      )}
                    </td>
                    <td className="px-3 py-2">
                      {entry.weather ? (
                        <div className="text-xs text-gray-900 max-w-xs truncate" title={entry.weather}>
                          {entry.weather}
                        </div>
                      ) : (
                        <span className="text-gray-400 text-xs">-</span>
                      )}
                    </td>
                    <td className="px-3 py-2 whitespace-nowrap">
                      {entry.isVoiceRecorded ? (
                        <span className="inline-flex items-center gap-1 px-1.5 py-0.5 bg-blue-100 text-blue-800 text-xs rounded-full">
                          <Mic className="h-2 w-2" />
                          Vocal
                        </span>
                      ) : (
                        <span className="inline-flex items-center px-1.5 py-0.5 bg-gray-100 text-gray-800 text-xs rounded-full">
                          Manuel
                        </span>
                      )}
                    </td>
                    <td className="px-3 py-2 whitespace-nowrap text-right text-sm font-medium">
                      <div className="flex justify-end space-x-1">
                        <button
                          onClick={() => setEditingEntry(entry.id)}
                          className="text-gray-400 hover:text-gray-600 p-1"
                          title="Modifier"
                        >
                          <Edit className="h-3 w-3" />
                        </button>
                        <button
                          onClick={() => deleteEntry(entry.id)}
                          className="text-gray-400 hover:text-red-600 p-1"
                          title="Supprimer"
                        >
                          <Trash2 className="h-3 w-3" />
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
                Décrivez votre intervention en détail : parcelle, type de traitement, conditions météo, observations...
              </p>
              <p className="text-xs text-muted mt-2">
                L'enregistrement sera automatiquement sauvegardé. Vous pourrez modifier les détails après.
              </p>
            </div>

            <VoiceInterface
              onVoiceMessage={handleVoiceMessage}
              className="py-4"
            />
          </div>
        </div>
      )}

      {/* Enhanced Voice Interface Modal */}
      {showEnhancedVoice && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold text-gray-900">Assistant Vocal (Nouveau)</h3>
              <button
                onClick={() => setShowEnhancedVoice(false)}
                className="text-gray-400 hover:text-gray-600 transition-colors"
              >
                <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <div className="mb-4">
              <p className="text-sm text-gray-600">
                Nouvelle interface vocale avec validation asynchrone. Enregistrez votre intervention 
                et recevez une validation en temps réel avec vérification EPHY et météo.
              </p>
              <p className="text-xs text-gray-500 mt-2">
                Exemple: "J'ai appliqué Saracen Delta sur la parcelle Nord ce matin"
              </p>
            </div>

            <EnhancedVoiceInterface
              onJournalEntry={handleEnhancedJournalEntry}
              mode="journal"
              className="py-4"
            />
          </div>
        </div>
      )}

      {/* Streaming Voice Assistant Modal */}
      {showStreamingVoice && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold text-gray-900">Assistant Vocal Intelligent</h3>
              <button
                onClick={() => setShowStreamingVoice(false)}
                className="text-gray-400 hover:text-gray-600 transition-colors"
              >
                <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <div className="mb-4">
              <p className="text-sm text-gray-600">
                Décrivez votre intervention agricole en détail. L'IA va extraire automatiquement les informations structurées 
                (parcelle, type d'intervention, produits utilisés, conditions météo, etc.) et valider la conformité.
              </p>
              <p className="text-xs text-gray-500 mt-2">
                Exemple: "J'ai appliqué du fongicide sur la parcelle Nord de 12 hectares ce matin. 
                Conditions ensoleillées, 18 degrés, vent faible. Utilisé 2 litres par hectare."
              </p>
            </div>

            <StreamingVoiceAssistant
              onJournalEntry={handleStreamingJournalEntry}
              mode="journal"
              className="py-4"
            />
          </div>
        </div>
      )}
    </div>
  )
}

export default VoiceJournal
