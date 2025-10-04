import React, { useState, useEffect, useRef } from 'react'
import { Mic, MicOff, Volume2, VolumeX, Loader2, CheckCircle, AlertTriangle, Clock } from 'lucide-react'

interface VoiceInterfaceProps {
  onJournalEntry?: (entry: any) => void
  onTranscript?: (text: string) => void
  className?: string
  mode?: 'journal' | 'chat'
}

interface JournalEntry {
  id: string
  transcript: string
  status: 'saved_pending_validation' | 'validated' | 'validation_failed'
  created_at: string
  validated_at?: string
  validation_results?: any
}

export const JournalVoiceInterface: React.FC<VoiceInterfaceProps> = ({
  onJournalEntry,
  onTranscript,
  className = '',
  mode = 'journal'
}) => {
  const [isListening, setIsListening] = useState(false)
  const [isProcessing, setIsProcessing] = useState(false)
  const [isSpeaking, setIsSpeaking] = useState(false)
  const [transcript, setTranscript] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [audioLevel, setAudioLevel] = useState(0)
  const [connectionStatus, setConnectionStatus] = useState<'disconnected' | 'connecting' | 'connected'>('disconnected')
  const [recentEntries, setRecentEntries] = useState<JournalEntry[]>([])
  
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const audioContextRef = useRef<AudioContext | null>(null)
  const analyserRef = useRef<AnalyserNode | null>(null)
  const audioChunksRef = useRef<Blob[]>([])
  const streamRef = useRef<MediaStream | null>(null)
  const audioRef = useRef<HTMLAudioElement | null>(null)
  const wsRef = useRef<WebSocket | null>(null)
  const connectionIdRef = useRef<string | null>(null)

  // WebSocket connection
  useEffect(() => {
    connectWebSocket()
    return () => {
      if (wsRef.current) {
        wsRef.current.close()
      }
    }
  }, [])

  const connectWebSocket = () => {
    try {
      setConnectionStatus('connecting')
      
      // Get WebSocket URL based on environment
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
      const host = window.location.host
      const wsUrl = `${protocol}//${host}/api/v1/voice/ws/voice/journal`
      
      wsRef.current = new WebSocket(wsUrl)
      
      wsRef.current.onopen = () => {
        setConnectionStatus('connected')
        setError(null)
        console.log('Voice WebSocket connected')
      }
      
      wsRef.current.onmessage = async (event) => {
        try {
          const data = JSON.parse(event.data)
          await handleWebSocketMessage(data)
        } catch (error) {
          console.error('Error parsing WebSocket message:', error)
        }
      }
      
      wsRef.current.onclose = () => {
        setConnectionStatus('disconnected')
        console.log('Voice WebSocket disconnected')
        // Attempt to reconnect after 3 seconds
        setTimeout(() => {
          if (connectionStatus !== 'connected') {
            connectWebSocket()
          }
        }, 3000)
      }
      
      wsRef.current.onerror = (error) => {
        console.error('WebSocket error:', error)
        setError('Erreur de connexion WebSocket')
        setConnectionStatus('disconnected')
      }
      
    } catch (error) {
      console.error('Error connecting WebSocket:', error)
      setError('Impossible de se connecter au serveur')
      setConnectionStatus('disconnected')
    }
  }

  const handleWebSocketMessage = async (data: any) => {
    console.log('WebSocket message:', data)
    
    switch (data.type) {
      case 'connection_established':
        connectionIdRef.current = data.connection_id
        break
        
      case 'user_transcript':
        setTranscript(data.text)
        if (data.is_final) {
          onTranscript?.(data.text)
        }
        break
        
      case 'journal_saved':
        const newEntry: JournalEntry = {
          id: data.entry_id,
          transcript: data.transcript,
          status: data.status,
          created_at: new Date().toISOString()
        }
        setRecentEntries(prev => [newEntry, ...prev.slice(0, 4)]) // Keep last 5 entries
        onJournalEntry?.(newEntry)
        setIsProcessing(false)
        break
        
      case 'ai_text_chunk':
        // Handle streaming text response
        break
        
      case 'audio_chunk':
        // Handle streaming audio
        await playAudioChunk(data.data)
        break
        
      case 'error':
        setError(data.message)
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
      
      // Request microphone permission
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
          sampleRate: 16000
        } 
      })
      
      streamRef.current = stream
      
      // Set up audio analysis for visual feedback
      setupAudioAnalysis(stream)
      
      // Set up MediaRecorder
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus'
      })
      
      mediaRecorderRef.current = mediaRecorder
      audioChunksRef.current = []
      
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data)
          // Send audio chunks in real-time
          sendAudioChunk(event.data)
        }
      }
      
      mediaRecorder.onstop = () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' })
        sendCompleteAudio(audioBlob)
      }
      
      // Start recording with small time slices for real-time streaming
      mediaRecorder.start(250) // Collect data every 250ms
      setIsListening(true)
      
      // Notify server that recording started
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
      setIsProcessing(true)
      
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
      
      // Notify server that recording stopped
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({
          type: 'stop_voice_input',
          timestamp: Date.now()
        }))
      }
    }
  }

  const sendAudioChunk = (audioChunk: Blob) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      // Convert blob to base64 for WebSocket transmission
      const reader = new FileReader()
      reader.onload = () => {
        const base64 = (reader.result as string).split(',')[1]
        wsRef.current?.send(JSON.stringify({
          type: 'audio_chunk',
          data: base64,
          timestamp: Date.now()
        }))
      }
      reader.readAsDataURL(audioChunk)
    }
  }

  const sendCompleteAudio = (audioBlob: Blob) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      const reader = new FileReader()
      reader.onload = () => {
        const base64 = (reader.result as string).split(',')[1]
        wsRef.current?.send(JSON.stringify({
          type: 'complete_audio',
          data: base64,
          timestamp: Date.now()
        }))
      }
      reader.readAsDataURL(audioBlob)
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
      
      // Convert base64 to ArrayBuffer
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
        setIsProcessing(false)
      }
      
    } catch (error) {
      console.error('Error playing audio chunk:', error)
      setIsSpeaking(false)
      setIsProcessing(false)
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
    if (audioContextRef.current) {
      audioContextRef.current.close()
      audioContextRef.current = null
      setIsSpeaking(false)
      setIsProcessing(false)
    }
  }

  const getStatusText = () => {
    if (error) return error
    if (connectionStatus === 'connecting') return 'Connexion en cours...'
    if (connectionStatus === 'disconnected') return 'Déconnecté - Cliquez pour reconnecter'
    if (isSpeaking) return 'Assistant en cours de réponse...'
    if (isProcessing) return 'Traitement en cours...'
    if (isListening) return 'Écoute en cours... Parlez maintenant'
    return mode === 'journal' ? 'Enregistrez votre intervention' : 'Appuyez pour parler'
  }

  const getStatusColor = () => {
    if (error) return 'text-red-600'
    if (connectionStatus === 'disconnected') return 'text-red-600'
    if (connectionStatus === 'connecting') return 'text-yellow-600'
    if (isSpeaking) return 'text-blue-600'
    if (isProcessing) return 'text-yellow-600'
    if (isListening) return 'text-green-600'
    return 'text-gray-600'
  }

  const getConnectionStatusIcon = () => {
    switch (connectionStatus) {
      case 'connected':
        return <CheckCircle className="h-4 w-4 text-green-500" />
      case 'connecting':
        return <Loader2 className="h-4 w-4 text-yellow-500 animate-spin" />
      case 'disconnected':
        return <AlertTriangle className="h-4 w-4 text-red-500" />
    }
  }

  const getEntryStatusIcon = (status: string) => {
    switch (status) {
      case 'validated':
        return <CheckCircle className="h-4 w-4 text-green-500" />
      case 'validation_failed':
        return <AlertTriangle className="h-4 w-4 text-red-500" />
      case 'saved_pending_validation':
        return <Clock className="h-4 w-4 text-yellow-500" />
      default:
        return <Clock className="h-4 w-4 text-gray-500" />
    }
  }

  return (
    <div className={`enhanced-voice-interface ${className}`}>
      {/* Connection Status */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-2">
          {getConnectionStatusIcon()}
          <span className="text-sm text-gray-600">
            {connectionStatus === 'connected' ? 'Connecté' : 
             connectionStatus === 'connecting' ? 'Connexion...' : 'Déconnecté'}
          </span>
        </div>
        
        {mode === 'journal' && (
          <span className="text-xs px-2 py-1 bg-orange-100 text-orange-800 rounded-full">
            Mode Journal
          </span>
        )}
      </div>

      {/* Main Voice Interface */}
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
            disabled={isProcessing && !isSpeaking || connectionStatus !== 'connected'}
            className={`relative w-20 h-20 rounded-full flex items-center justify-center transition-all duration-200 ${
              isListening 
                ? 'bg-red-600 hover:bg-red-700 text-white' 
                : isSpeaking
                ? 'bg-blue-600 hover:bg-blue-700 text-white'
                : isProcessing
                ? 'bg-yellow-600 text-white cursor-not-allowed'
                : connectionStatus === 'connected'
                ? 'bg-green-600 hover:bg-green-700 text-white'
                : 'bg-gray-400 text-white cursor-not-allowed'
            }`}
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
        <div className="text-center">
          <p className={`text-sm font-medium ${getStatusColor()}`}>
            {getStatusText()}
          </p>
          
          {/* Transcript */}
          {transcript && (
            <div className="mt-3 p-3 bg-gray-100 rounded-lg max-w-md">
              <p className="text-sm text-gray-800">{transcript}</p>
            </div>
          )}
        </div>
      </div>

      {/* Recent Entries (Journal Mode) */}
      {mode === 'journal' && recentEntries.length > 0 && (
        <div className="mt-6">
          <h3 className="text-sm font-medium text-gray-700 mb-2">Entrées récentes</h3>
          <div className="space-y-2">
            {recentEntries.map((entry) => (
              <div key={entry.id} className="flex items-center space-x-3 p-2 bg-gray-50 rounded-lg">
                {getEntryStatusIcon(entry.status)}
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-gray-800 truncate">{entry.transcript}</p>
                  <p className="text-xs text-gray-500">
                    {new Date(entry.created_at).toLocaleTimeString()}
                  </p>
                </div>
                <span className={`text-xs px-2 py-1 rounded-full ${
                  entry.status === 'validated' ? 'bg-green-100 text-green-800' :
                  entry.status === 'validation_failed' ? 'bg-red-100 text-red-800' :
                  'bg-yellow-100 text-yellow-800'
                }`}>
                  {entry.status === 'validated' ? 'Validé' :
                   entry.status === 'validation_failed' ? 'Erreur' :
                   'En cours'}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

export default EnhancedVoiceInterface
