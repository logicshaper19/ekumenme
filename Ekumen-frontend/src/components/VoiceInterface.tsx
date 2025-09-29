import React, { useState, useEffect, useRef } from 'react'
import { Mic, MicOff, Volume2, VolumeX, Loader2, Play, Pause } from 'lucide-react'
import { useWebSocket } from '../services/websocket'

interface VoiceInterfaceProps {
  onTranscript?: (text: string) => void
  onVoiceMessage?: (message: string) => void
  className?: string
}

export const VoiceInterface: React.FC<VoiceInterfaceProps> = ({
  onTranscript,
  onVoiceMessage,
  className = ''
}) => {
  const [isListening, setIsListening] = useState(false)
  const [isProcessing, setIsProcessing] = useState(false)
  const [isSpeaking, setIsSpeaking] = useState(false)
  const [transcript, setTranscript] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [audioLevel, setAudioLevel] = useState(0)
  
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const audioContextRef = useRef<AudioContext | null>(null)
  const analyserRef = useRef<AnalyserNode | null>(null)
  const audioChunksRef = useRef<Blob[]>([])
  const streamRef = useRef<MediaStream | null>(null)
  const audioRef = useRef<HTMLAudioElement | null>(null)
  
  const webSocket = useWebSocket()

  useEffect(() => {
    // Set up WebSocket event listeners
    webSocket.onVoiceTranscript((data) => {
      setTranscript(data.text)
      if (data.is_final) {
        onTranscript?.(data.text)
        if (data.text.trim()) {
          onVoiceMessage?.(data.text)
        }
      }
    })

    webSocket.onVoiceResponse((data) => {
      playAudioResponse(data.audio)
    })

    webSocket.onError((data) => {
      setError(data.message)
      setIsProcessing(false)
      setIsListening(false)
    })

    return () => {
      webSocket.off('voice:transcript')
      webSocket.off('voice:response')
      webSocket.off('error')
    }
  }, [webSocket, onTranscript, onVoiceMessage])

  const startListening = async () => {
    try {
      setError(null)
      
      // Request microphone permission
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true
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
        }
      }
      
      mediaRecorder.onstop = () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' })
        sendAudioToServer(audioBlob)
      }
      
      // Start recording
      mediaRecorder.start(1000) // Collect data every second
      setIsListening(true)
      
      // Notify server
      webSocket.startVoiceInput()
      
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
      
      // Notify server
      webSocket.stopVoiceInput()
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

  const sendAudioToServer = (audioBlob: Blob) => {
    try {
      webSocket.sendVoiceData(audioBlob)
    } catch (error) {
      console.error('Error sending audio to server:', error)
      setError('Erreur lors de l\'envoi de l\'audio')
      setIsProcessing(false)
    }
  }

  const playAudioResponse = (audioBlob: Blob) => {
    try {
      const audioUrl = URL.createObjectURL(audioBlob)
      const audio = new Audio(audioUrl)
      
      audioRef.current = audio
      
      audio.onplay = () => setIsSpeaking(true)
      audio.onended = () => {
        setIsSpeaking(false)
        setIsProcessing(false)
        URL.revokeObjectURL(audioUrl)
      }
      audio.onerror = () => {
        setError('Erreur lors de la lecture de la réponse audio')
        setIsSpeaking(false)
        setIsProcessing(false)
      }
      
      audio.play()
    } catch (error) {
      console.error('Error playing audio response:', error)
      setError('Erreur lors de la lecture de la réponse')
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
    if (audioRef.current) {
      audioRef.current.pause()
      audioRef.current.currentTime = 0
      setIsSpeaking(false)
      setIsProcessing(false)
    }
  }

  const getStatusText = () => {
    if (error) return error
    if (isSpeaking) return 'Assistant en cours de réponse...'
    if (isProcessing) return 'Traitement en cours...'
    if (isListening) return 'Écoute en cours... Parlez maintenant'
    return 'Appuyez pour parler'
  }

  const getStatusColor = () => {
    if (error) return 'text-red-600'
    if (isSpeaking) return 'text-blue-600'
    if (isProcessing) return 'text-yellow-600'
    if (isListening) return 'text-green-600'
    return 'text-gray-600'
  }

  return (
    <div className={`voice-interface ${className}`}>
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
            disabled={isProcessing && !isSpeaking}
            className={`relative w-16 h-16 rounded-full flex items-center justify-center transition-all duration-200 ${
              isListening 
                ? 'bg-red-600 hover:bg-red-700 text-white' 
                : isSpeaking
                ? 'bg-blue-600 hover:bg-blue-700 text-white'
                : isProcessing
                ? 'bg-yellow-600 text-white cursor-not-allowed'
                : 'bg-green-600 hover:bg-green-700 text-white'
            }`}
          >
            {isProcessing && !isSpeaking ? (
              <Loader2 className="h-6 w-6 animate-spin" />
            ) : isSpeaking ? (
              <VolumeX className="h-6 w-6" />
            ) : isListening ? (
              <MicOff className="h-6 w-6" />
            ) : (
              <Mic className="h-6 w-6" />
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
            <div className="mt-2 p-3 bg-gray-100 rounded-lg max-w-md">
              <p className="text-sm text-gray-800">{transcript}</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default VoiceInterface
