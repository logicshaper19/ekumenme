import React, { useState, useEffect, useRef, useCallback } from 'react'
import { Mic, MicOff, Volume2, VolumeX, Loader2, Play, Pause, MessageSquare } from 'lucide-react'
import InterventionConfirmationModal from './InterventionConfirmationModal'

interface StreamingVoiceAssistantProps {
  onTranscript?: (text: string) => void
  onVoiceMessage?: (message: string) => void
  onJournalEntry?: (entry: any) => void
  mode?: 'chat' | 'journal'
  className?: string
}

interface VoiceMessage {
  type: string
  text?: string
  data?: string
  message?: string
  timestamp?: number
}

export const StreamingVoiceAssistant: React.FC<StreamingVoiceAssistantProps> = ({
  onTranscript,
  onVoiceMessage,
  onJournalEntry,
  mode = 'chat',
  className = ''
}) => {
  const [isListening, setIsListening] = useState(false)
  const [isProcessing, setIsProcessing] = useState(false)
  const [isSpeaking, setIsSpeaking] = useState(false)
  const [transcript, setTranscript] = useState('')
  const [aiResponse, setAiResponse] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [audioLevel, setAudioLevel] = useState(0)
  const [connectionStatus, setConnectionStatus] = useState<'disconnected' | 'connecting' | 'connected'>('disconnected')
  
  // Confirmation modal state
  const [showConfirmationModal, setShowConfirmationModal] = useState(false)
  const [confirmationData, setConfirmationData] = useState<any>(null)
  const [validationResults, setValidationResults] = useState<any[]>([])
  const [confirmationQuestions, setConfirmationQuestions] = useState<any[]>([])
  const [voiceConfirmation, setVoiceConfirmation] = useState('')
  
  const wsRef = useRef<WebSocket | null>(null)
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const audioContextRef = useRef<AudioContext | null>(null)
  const analyserRef = useRef<AnalyserNode | null>(null)
  const audioQueueRef = useRef<HTMLAudioElement[]>([])
  const streamRef = useRef<MediaStream | null>(null)
  const audioChunksRef = useRef<Blob[]>([])
  const connectionIdRef = useRef<string | null>(null)

  // WebSocket connection management
  const connectWebSocket = useCallback(async () => {
    try {
      setConnectionStatus('connecting')
      setError(null)
      
      // Get auth token
      const token = localStorage.getItem('auth_token')
      if (!token) {
        throw new Error('No authentication token found')
      }
      
      // Connect to appropriate WebSocket endpoint
      const endpoint = mode === 'journal' 
        ? `/api/v1/voice/ws/voice/journal?token=${token}`
        : `/api/v1/voice/ws/voice?token=${token}`
      
      const wsUrl = `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}${endpoint}`
      
      wsRef.current = new WebSocket(wsUrl)
      
      wsRef.current.onopen = () => {
        setConnectionStatus('connected')
        console.log('Voice WebSocket connected')
      }
      
      wsRef.current.onmessage = async (event) => {
        try {
          const data: VoiceMessage = JSON.parse(event.data)
          await handleWebSocketMessage(data)
        } catch (error) {
          console.error('Error parsing WebSocket message:', error)
        }
      }
      
      wsRef.current.onclose = () => {
        setConnectionStatus('disconnected')
        setIsListening(false)
        setIsProcessing(false)
        console.log('Voice WebSocket disconnected')
      }
      
      wsRef.current.onerror = (error) => {
        setConnectionStatus('disconnected')
        setError('Connection error')
        console.error('Voice WebSocket error:', error)
      }
      
    } catch (error) {
      setConnectionStatus('disconnected')
      setError(`Connection failed: ${error}`)
      console.error('WebSocket connection error:', error)
    }
  }, [mode])

  const handleWebSocketMessage = async (data: VoiceMessage) => {
    switch (data.type) {
      case 'connection':
        connectionIdRef.current = data.message
        console.log('Connected to voice assistant:', data.message)
        break
        
      case 'user_transcript':
        setTranscript(data.text || '')
        if (data.text && onTranscript) {
          onTranscript(data.text)
        }
        break
        
      case 'ai_text_chunk':
        setAiResponse(prev => prev + (data.text || ''))
        break
        
      case 'ai_response_started':
        setIsProcessing(true)
        setAiResponse('')
        break
        
      case 'ai_response_complete':
        setIsProcessing(false)
        if (aiResponse && onVoiceMessage) {
          onVoiceMessage(aiResponse)
        }
        break
        
      case 'audio_chunk':
        if (data.data) {
          await playAudioChunk(data.data)
        }
        break
        
      case 'journal_data_extracted':
        if (onJournalEntry) {
          onJournalEntry(data)
        }
        break
        
        case 'journal_validation':
          console.log('Journal validation:', data)
          setValidationResults(data.result?.validation_results || [])
          setVoiceConfirmation(data.result?.voice_confirmation || '')
          break
          
        case 'confirmation_required':
          setConfirmationData(data)
          setConfirmationQuestions(data.questions || [])
          setShowConfirmationModal(true)
          break
          
        case 'journal_saved':
          console.log('Journal entry saved:', data)
          setShowConfirmationModal(false)
          break
          
        case 'final_validation':
          console.log('Final validation:', data)
          break
          
        case 'intervention_rejected':
          console.log('Intervention rejected:', data)
          setShowConfirmationModal(false)
          break
        
      case 'processing_started':
        setIsProcessing(true)
        break
        
      case 'error':
        setError(data.message || 'Unknown error')
        setIsProcessing(false)
        setIsListening(false)
        break
        
      default:
        console.log('Unknown message type:', data.type)
    }
  }

  const startListening = async () => {
    try {
      setError(null)
      
      if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
        await connectWebSocket()
        // Wait a bit for connection to establish
        await new Promise(resolve => setTimeout(resolve, 1000))
      }
      
      // Request microphone permission
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
          channelCount: 1,
          sampleRate: 16000
        } 
      })
      
      streamRef.current = stream
      
      // Set up audio analysis for visual feedback
      setupAudioAnalysis(stream)
      
      // Set up MediaRecorder for streaming
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus'
      })
      
      mediaRecorderRef.current = mediaRecorder
      audioChunksRef.current = []
      
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          // Send audio chunks directly to WebSocket
          if (wsRef.current?.readyState === WebSocket.OPEN) {
            wsRef.current.send(event.data)
          }
        }
      }
      
      // Start recording with small time slices for real-time streaming
      mediaRecorder.start(250) // Send chunks every 250ms
      setIsListening(true)
      
      // Notify server that we're starting voice input
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({
          type: 'start_voice_input',
          timestamp: Date.now()
        }))
      }
      
    } catch (error) {
      console.error('Error starting voice input:', error)
      setError('Impossible d\'accéder au microphone. Vérifiez les permissions.')
    }
  }

  const stopListening = () => {
    if (mediaRecorderRef.current && isListening) {
      mediaRecorderRef.current.stop()
      setIsListening(false)
      
      // Stop audio analysis
      if (audioContextRef.current) {
        audioContextRef.current.close()
        audioContextRef.current = null
      }
      
      // Stop media stream
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop())
        streamRef.current = null
      }
      
      // Notify server that we stopped voice input
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({
          type: 'stop_voice_input',
          timestamp: Date.now()
        }))
      }
    }
  }

  const setupAudioAnalysis = (stream: MediaStream) => {
    try {
      const audioContext = new AudioContext()
      const analyser = audioContext.createAnalyser()
      const microphone = audioContext.createMediaStreamSource(stream)
      
      analyser.fftSize = 256
      microphone.connect(analyser)
      
      audioContextRef.current = audioContext
      analyserRef.current = analyser
      
      // Start monitoring audio levels
      monitorAudioLevel()
    } catch (error) {
      console.error('Error setting up audio analysis:', error)
    }
  }

  const monitorAudioLevel = () => {
    if (!analyserRef.current) return
    
    const dataArray = new Uint8Array(analyserRef.current.frequencyBinCount)
    
    const updateLevel = () => {
      if (!analyserRef.current || !isListening) return
      
      analyserRef.current.getByteFrequencyData(dataArray)
      const average = dataArray.reduce((sum, value) => sum + value, 0) / dataArray.length
      setAudioLevel(average / 255) // Normalize to 0-1
      
      requestAnimationFrame(updateLevel)
    }
    
    updateLevel()
  }

  const playAudioChunk = async (base64Data: string) => {
    try {
      if (!audioContextRef.current) {
        audioContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)()
      }
      
      const audioContext = audioContextRef.current
      
      // Convert base64 to bytes
      const binaryString = atob(base64Data)
      const bytes = new Uint8Array(binaryString.length)
      for (let i = 0; i < binaryString.length; i++) {
        bytes[i] = binaryString.charCodeAt(i)
      }
      
      // Decode audio
      const audioBuffer = await audioContext.decodeAudioData(bytes.buffer)
      
      // Create audio source
      const source = audioContext.createBufferSource()
      source.buffer = audioBuffer
      source.connect(audioContext.destination)
      
      // Play immediately
      setIsSpeaking(true)
      source.start(0)
      source.onended = () => {
        setIsSpeaking(false)
      }
      
    } catch (error) {
      console.error('Error playing audio chunk:', error)
      setIsSpeaking(false)
    }
  }

  const toggleListening = () => {
    if (isListening) {
      stopListening()
    } else {
      startListening()
    }
  }

  const stopSpeaking = () => {
    // Stop all audio playback
    audioQueueRef.current.forEach(audio => {
      audio.pause()
      audio.currentTime = 0
    })
    audioQueueRef.current = []
    setIsSpeaking(false)
  }

  const clearConversation = () => {
    setTranscript('')
    setAiResponse('')
    setError(null)
  }

  const handleConfirmationResponse = async (responses: any) => {
    try {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({
          type: 'confirmation_response',
          intervention_data: confirmationData,
          responses: responses,
          timestamp: Date.now()
        }))
      }
    } catch (error) {
      console.error('Error sending confirmation response:', error)
    }
  }

  const handleSaveIntervention = async (data: any) => {
    try {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({
          type: 'save_intervention',
          intervention_data: data,
          timestamp: Date.now()
        }))
      }
    } catch (error) {
      console.error('Error saving intervention:', error)
    }
  }

  const handleVoicePlayback = async (text: string) => {
    // This would integrate with your TTS service
    console.log('Playing voice confirmation:', text)
  }

  const getStatusText = () => {
    if (error) return error
    if (connectionStatus === 'connecting') return 'Connexion en cours...'
    if (connectionStatus === 'disconnected') return 'Déconnecté - Cliquez pour reconnecter'
    if (isSpeaking) return 'Assistant en cours de réponse...'
    if (isProcessing) return 'Traitement en cours...'
    if (isListening) return 'Écoute en cours... Parlez maintenant'
    return mode === 'journal' ? 'Enregistrez votre activité agricole' : 'Appuyez pour parler'
  }

  const getStatusColor = () => {
    if (error) return 'text-red-600'
    if (connectionStatus === 'disconnected') return 'text-gray-500'
    if (connectionStatus === 'connecting') return 'text-yellow-600'
    if (isSpeaking) return 'text-blue-600'
    if (isProcessing) return 'text-yellow-600'
    if (isListening) return 'text-green-600'
    return 'text-gray-600'
  }

  const getButtonColor = () => {
    if (error || connectionStatus === 'disconnected') return 'bg-gray-600 hover:bg-gray-700'
    if (isSpeaking) return 'bg-blue-600 hover:bg-blue-700'
    if (isProcessing) return 'bg-yellow-600 cursor-not-allowed'
    if (isListening) return 'bg-red-600 hover:bg-red-700'
    return 'bg-green-600 hover:bg-green-700'
  }

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (wsRef.current) {
        wsRef.current.close()
      }
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop())
      }
      if (audioContextRef.current) {
        audioContextRef.current.close()
      }
    }
  }, [])

  return (
    <div className={`streaming-voice-assistant ${className}`}>
      {/* Connection Status */}
      <div className="mb-4 text-center">
        <div className={`inline-flex items-center px-3 py-1 rounded-full text-sm ${
          connectionStatus === 'connected' ? 'bg-green-100 text-green-800' :
          connectionStatus === 'connecting' ? 'bg-yellow-100 text-yellow-800' :
          'bg-red-100 text-red-800'
        }`}>
          <div className={`w-2 h-2 rounded-full mr-2 ${
            connectionStatus === 'connected' ? 'bg-green-500' :
            connectionStatus === 'connecting' ? 'bg-yellow-500 animate-pulse' :
            'bg-red-500'
          }`} />
          {connectionStatus === 'connected' ? 'Connecté' :
           connectionStatus === 'connecting' ? 'Connexion...' :
           'Déconnecté'}
        </div>
      </div>

      {/* Main Voice Button */}
      <div className="flex flex-col items-center space-y-4">
        <div className="relative">
          {/* Audio Level Visualization */}
          {isListening && (
            <div 
              className="absolute inset-0 rounded-full bg-green-400 opacity-30 animate-pulse"
              style={{
                transform: `scale(${1 + audioLevel * 0.5})`,
                transition: 'transform 0.1s ease-out'
              }}
            />
          )}
          
          {/* Main Button */}
          <button
            onClick={isSpeaking ? stopSpeaking : toggleListening}
            disabled={isProcessing && !isSpeaking || connectionStatus === 'connecting'}
            className={`relative w-20 h-20 rounded-full flex items-center justify-center transition-all duration-200 text-white ${getButtonColor()}`}
          >
            {isProcessing && !isSpeaking ? (
              <Loader2 className="h-8 w-8 animate-spin" />
            ) : isSpeaking ? (
              <VolumeX className="h-8 w-8" />
            ) : isListening ? (
              <MicOff className="h-8 w-8" />
            ) : (
              <Mic className="h-8 w-8" />
            )}
          </button>
        </div>

        {/* Status Text */}
        <div className="text-center max-w-md">
          <p className={`text-sm font-medium ${getStatusColor()}`}>
            {getStatusText()}
          </p>
        </div>
      </div>

      {/* Conversation Display */}
      {(transcript || aiResponse) && (
        <div className="mt-6 space-y-4">
          {/* User Transcript */}
          {transcript && (
            <div className="bg-blue-50 rounded-lg p-4">
              <div className="flex items-center mb-2">
                <MessageSquare className="h-4 w-4 text-blue-600 mr-2" />
                <span className="text-sm font-medium text-blue-800">Vous:</span>
              </div>
              <p className="text-sm text-blue-900">{transcript}</p>
            </div>
          )}
          
          {/* AI Response */}
          {aiResponse && (
            <div className="bg-green-50 rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center">
                  <Volume2 className="h-4 w-4 text-green-600 mr-2" />
                  <span className="text-sm font-medium text-green-800">Assistant:</span>
                </div>
                {isSpeaking && <span className="text-xs text-green-600">🔊 En cours de lecture</span>}
              </div>
              <p className="text-sm text-green-900">{aiResponse}</p>
            </div>
          )}
          
          {/* Clear Button */}
          <div className="text-center">
            <button
              onClick={clearConversation}
              className="text-xs text-gray-500 hover:text-gray-700 underline"
            >
              Effacer la conversation
            </button>
          </div>
        </div>
      )}

      {/* Mode Indicator */}
      <div className="mt-4 text-center">
        <span className={`text-xs px-2 py-1 rounded-full ${
          mode === 'journal' 
            ? 'bg-orange-100 text-orange-800' 
            : 'bg-blue-100 text-blue-800'
        }`}>
          {mode === 'journal' ? 'Mode Journal' : 'Mode Chat'}
        </span>
      </div>

      {/* Confirmation Modal */}
      <InterventionConfirmationModal
        isOpen={showConfirmationModal}
        onClose={() => setShowConfirmationModal(false)}
        interventionData={confirmationData}
        validationResults={validationResults}
        confirmationQuestions={confirmationQuestions}
        voiceConfirmation={voiceConfirmation}
        onConfirm={handleConfirmationResponse}
        onSave={handleSaveIntervention}
        onVoicePlayback={handleVoicePlayback}
      />
    </div>
  )
}

export default StreamingVoiceAssistant
