import React, { useState, useEffect } from 'react'
import { CheckCircle, AlertTriangle, XCircle, Info, Mic, Volume2, Edit3, Save } from 'lucide-react'

interface ValidationResult {
  is_valid: boolean
  level: 'info' | 'warning' | 'error' | 'critical'
  message: string
  field: string
  suggested_value?: any
}

interface ConfirmationQuestion {
  type: 'confirmation' | 'clarification' | 'acknowledgment'
  question: string
  field?: string
  level: 'info' | 'warning' | 'error' | 'critical'
  requires_explicit_confirmation?: boolean
  suggested_prompt?: string
  details?: Array<{ field: string; message: string }>
}

interface InterventionConfirmationModalProps {
  isOpen: boolean
  onClose: () => void
  interventionData: any
  validationResults: ValidationResult[]
  confirmationQuestions: ConfirmationQuestion[]
  voiceConfirmation: string
  onConfirm: (responses: any) => void
  onSave: (data: any) => void
  onVoicePlayback?: (text: string) => void
}

export const InterventionConfirmationModal: React.FC<InterventionConfirmationModalProps> = ({
  isOpen,
  onClose,
  interventionData,
  validationResults,
  confirmationQuestions,
  voiceConfirmation,
  onConfirm,
  onSave,
  onVoicePlayback
}) => {
  const [responses, setResponses] = useState<Record<string, any>>({})
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0)
  const [isPlayingVoice, setIsPlayingVoice] = useState(false)

  useEffect(() => {
    if (isOpen) {
      setResponses({})
      setCurrentQuestionIndex(0)
    }
  }, [isOpen])

  const getValidationIcon = (level: string) => {
    switch (level) {
      case 'error':
      case 'critical':
        return <XCircle className="h-5 w-5 text-red-500" />
      case 'warning':
        return <AlertTriangle className="h-5 w-5 text-yellow-500" />
      case 'info':
        return <Info className="h-5 w-5 text-blue-500" />
      default:
        return <CheckCircle className="h-5 w-5 text-green-500" />
    }
  }

  const getValidationColor = (level: string) => {
    switch (level) {
      case 'error':
      case 'critical':
        return 'border-red-200 bg-red-50'
      case 'warning':
        return 'border-yellow-200 bg-yellow-50'
      case 'info':
        return 'border-blue-200 bg-blue-50'
      default:
        return 'border-green-200 bg-green-50'
    }
  }

  const handleResponse = (questionIndex: number, response: any) => {
    const question = confirmationQuestions[questionIndex]
    setResponses(prev => ({
      ...prev,
      [question.field || `question_${questionIndex}`]: response
    }))
  }

  const handleNextQuestion = () => {
    if (currentQuestionIndex < confirmationQuestions.length - 1) {
      setCurrentQuestionIndex(currentQuestionIndex + 1)
    } else {
      // All questions answered, proceed with confirmation
      onConfirm(responses)
    }
  }

  const handlePlayVoiceConfirmation = async () => {
    if (onVoicePlayback) {
      setIsPlayingVoice(true)
      await onVoicePlayback(voiceConfirmation)
      setIsPlayingVoice(false)
    }
  }

  const canProceed = validationResults.filter(r => r.level === 'error' || r.level === 'critical').length === 0

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex justify-between items-center p-6 border-b">
          <h2 className="text-xl font-semibold text-gray-900">
            Confirmation d'Intervention
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <XCircle className="h-6 w-6" />
          </button>
        </div>

        <div className="p-6 space-y-6">
          {/* Voice Confirmation Section */}
          <div className="bg-gray-50 rounded-lg p-4">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-lg font-medium text-gray-900 flex items-center">
                <Volume2 className="h-5 w-5 mr-2" />
                Résumé Vocal
              </h3>
              <button
                onClick={handlePlayVoiceConfirmation}
                disabled={isPlayingVoice}
                className="flex items-center px-3 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
              >
                <Mic className="h-4 w-4 mr-2" />
                {isPlayingVoice ? 'Lecture...' : 'Écouter'}
              </button>
            </div>
            <p className="text-gray-700 text-sm leading-relaxed">
              {voiceConfirmation}
            </p>
          </div>

          {/* Intervention Summary */}
          <div className="bg-white border rounded-lg p-4">
            <h3 className="text-lg font-medium text-gray-900 mb-3">Résumé de l'Intervention</h3>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="font-medium text-gray-600">Type:</span>
                <span className="ml-2 text-gray-900">{interventionData.type_intervention}</span>
              </div>
              <div>
                <span className="font-medium text-gray-600">Parcelle:</span>
                <span className="ml-2 text-gray-900">{interventionData.parcelle}</span>
              </div>
              <div>
                <span className="font-medium text-gray-600">Date:</span>
                <span className="ml-2 text-gray-900">{interventionData.date_intervention}</span>
              </div>
              <div>
                <span className="font-medium text-gray-600">Surface:</span>
                <span className="ml-2 text-gray-900">{interventionData.surface_travaillee_ha} ha</span>
              </div>
              <div>
                <span className="font-medium text-gray-600">Culture:</span>
                <span className="ml-2 text-gray-900">{interventionData.culture}</span>
              </div>
            </div>
          </div>

          {/* Products Used */}
          {interventionData.intrants && interventionData.intrants.length > 0 && (
            <div className="bg-white border rounded-lg p-4">
              <h3 className="text-lg font-medium text-gray-900 mb-3">Produits Utilisés</h3>
              <div className="space-y-2">
                {interventionData.intrants.map((intrant: any, index: number) => (
                  <div key={index} className="flex justify-between items-center p-3 bg-gray-50 rounded">
                    <div>
                      <span className="font-medium">{intrant.libelle}</span>
                      {intrant.code_amm && (
                        <span className="ml-2 text-sm text-gray-600">(AMM: {intrant.code_amm})</span>
                      )}
                    </div>
                    <div className="text-sm text-gray-600">
                      {intrant.quantite_totale} {intrant.unite_intrant_intervention}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Validation Results */}
          {validationResults.length > 0 && (
            <div className="bg-white border rounded-lg p-4">
              <h3 className="text-lg font-medium text-gray-900 mb-3">Validation</h3>
              <div className="space-y-3">
                {validationResults.map((result, index) => (
                  <div
                    key={index}
                    className={`flex items-start p-3 border rounded-lg ${getValidationColor(result.level)}`}
                  >
                    {getValidationIcon(result.level)}
                    <div className="ml-3">
                      <p className="text-sm font-medium text-gray-900">
                        {result.field}
                      </p>
                      <p className="text-sm text-gray-700">
                        {result.message}
                      </p>
                      {result.suggested_value && (
                        <p className="text-xs text-gray-600 mt-1">
                          Suggestion: {result.suggested_value}
                        </p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Confirmation Questions */}
          {confirmationQuestions.length > 0 && (
            <div className="bg-white border rounded-lg p-4">
              <h3 className="text-lg font-medium text-gray-900 mb-3">
                Questions de Confirmation ({currentQuestionIndex + 1}/{confirmationQuestions.length})
              </h3>
              
              {currentQuestionIndex < confirmationQuestions.length && (
                <div className="space-y-4">
                  {(() => {
                    const question = confirmationQuestions[currentQuestionIndex]
                    return (
                      <div className={`p-4 border rounded-lg ${getValidationColor(question.level)}`}>
                        <div className="flex items-start">
                          {getValidationIcon(question.level)}
                          <div className="ml-3 flex-1">
                            <p className="text-sm font-medium text-gray-900 mb-2">
                              {question.question}
                            </p>
                            
                            {question.type === 'confirmation' && (
                              <div className="flex space-x-3">
                                <button
                                  onClick={() => {
                                    handleResponse(currentQuestionIndex, true)
                                    handleNextQuestion()
                                  }}
                                  className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700"
                                >
                                  Oui, confirmer
                                </button>
                                <button
                                  onClick={() => {
                                    handleResponse(currentQuestionIndex, false)
                                    onClose()
                                  }}
                                  className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700"
                                >
                                  Non, annuler
                                </button>
                              </div>
                            )}
                            
                            {question.type === 'clarification' && (
                              <div className="space-y-2">
                                <input
                                  type="text"
                                  placeholder={question.suggested_prompt}
                                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                  onChange={(e) => handleResponse(currentQuestionIndex, e.target.value)}
                                />
                                <button
                                  onClick={handleNextQuestion}
                                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                                >
                                  Continuer
                                </button>
                              </div>
                            )}
                            
                            {question.type === 'acknowledgment' && (
                              <div className="space-y-2">
                                {question.details && (
                                  <div className="text-xs text-gray-600">
                                    {question.details.map((detail, idx) => (
                                      <div key={idx}>• {detail.message}</div>
                                    ))}
                                  </div>
                                )}
                                <div className="flex space-x-3">
                                  <button
                                    onClick={() => {
                                      handleResponse(currentQuestionIndex, true)
                                      handleNextQuestion()
                                    }}
                                    className="px-4 py-2 bg-yellow-600 text-white rounded-md hover:bg-yellow-700"
                                  >
                                    Continuer malgré les avertissements
                                  </button>
                                  <button
                                    onClick={onClose}
                                    className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700"
                                  >
                                    Modifier
                                  </button>
                                </div>
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    )
                  })()}
                </div>
              )}
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex justify-between items-center pt-4 border-t">
            <button
              onClick={onClose}
              className="px-4 py-2 text-gray-600 hover:text-gray-800"
            >
              Annuler
            </button>
            
            <div className="flex space-x-3">
              {confirmationQuestions.length === 0 && (
                <button
                  onClick={() => onSave(interventionData)}
                  disabled={!canProceed}
                  className={`flex items-center px-4 py-2 rounded-md ${
                    canProceed
                      ? 'bg-green-600 text-white hover:bg-green-700'
                      : 'bg-gray-300 text-gray-500 cursor-not-allowed'
                  }`}
                >
                  <Save className="h-4 w-4 mr-2" />
                  Enregistrer
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default InterventionConfirmationModal
