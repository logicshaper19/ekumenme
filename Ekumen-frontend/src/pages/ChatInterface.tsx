import React, { useState, useEffect, useRef } from 'react'
import { Send, Bot, User, Loader2 } from 'lucide-react'
import { useWebSocket } from '../services/websocket'
import VoiceInterface from '../components/VoiceInterface'

interface Message {
  id: string
  content: string
  sender: 'user' | 'assistant'
  timestamp: Date
  agent?: string
  agentName?: string
  isStreaming?: boolean
}

interface AgentInfo {
  type: string
  name: string
  icon: string
  description: string
}

const ChatInterface: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([])
  const [inputValue, setInputValue] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [currentAgent, setCurrentAgent] = useState<AgentInfo | null>(null)
  const [isStreaming, setIsStreaming] = useState(false)
  const [showVoiceInterface, setShowVoiceInterface] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const webSocket = useWebSocket()

  const agents: Record<string, AgentInfo> = {
    farm_data: { type: 'farm_data', name: 'Données d\'Exploitation', icon: '🌾', description: 'Analyse de parcelles et interventions' },
    weather: { type: 'weather', name: 'Météorologie', icon: '🌤️', description: 'Prévisions et fenêtres d\'intervention' },
    crop_health: { type: 'crop_health', name: 'Santé des Cultures', icon: '🌱', description: 'Diagnostic et protection' },
    planning: { type: 'planning', name: 'Planification', icon: '📋', description: 'Organisation des activités' },
    regulatory: { type: 'regulatory', name: 'Conformité', icon: '⚖️', description: 'Réglementation et AMM' },
    sustainability: { type: 'sustainability', name: 'Durabilité', icon: '🌍', description: 'Impact environnemental' }
  }

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  useEffect(() => {
    // Initialize conversation
    const conversationId = 'default-conversation' // In real app, get from user session
    webSocket.joinConversation(conversationId)

    // Set up WebSocket event listeners
    webSocket.onMessageResponse((data) => {
      const assistantMessage: Message = {
        id: data.message.id,
        content: data.message.content,
        sender: 'assistant',
        timestamp: new Date(data.message.timestamp),
        agent: data.agent,
        agentName: agents[data.agent]?.name
      }

      setMessages(prev => [...prev, assistantMessage])
      setIsLoading(false)
      setIsStreaming(false)
    })

    webSocket.onStreamingStart((data) => {
      const assistantMessage: Message = {
        id: data.message_id,
        content: '',
        sender: 'assistant',
        timestamp: new Date(),
        isStreaming: true
      }

      setMessages(prev => [...prev, assistantMessage])
    })

    webSocket.onStreamingChunk((data) => {
      setMessages(prev => prev.map(msg =>
        msg.id === data.message_id
          ? { ...msg, content: msg.content + data.chunk }
          : msg
      ))

      if (data.is_complete) {
        setMessages(prev => prev.map(msg =>
          msg.id === data.message_id
            ? { ...msg, isStreaming: false }
            : msg
        ))
        setIsLoading(false)
        setIsStreaming(false)
      }
    })

    webSocket.onAgentSelected((data) => {
      setCurrentAgent({
        type: data.agent_type,
        name: data.agent_name,
        icon: agents[data.agent_type]?.icon || '🤖',
        description: agents[data.agent_type]?.description || ''
      })
    })

    webSocket.onError((data) => {
      console.error('WebSocket error:', data)
      const errorMessage: Message = {
        id: Date.now().toString(),
        content: `Erreur: ${data.message}`,
        sender: 'assistant',
        timestamp: new Date()
      }

      setMessages(prev => [...prev, errorMessage])
      setIsLoading(false)
      setIsStreaming(false)
    })

    return () => {
      webSocket.off('chat:message_response')
      webSocket.off('chat:streaming_start')
      webSocket.off('chat:streaming_chunk')
      webSocket.off('chat:agent_selected')
      webSocket.off('error')
    }
  }, [webSocket])

  // Smart agent selection based on message content
  const selectAgentForMessage = (message: string): AgentInfo => {
    const messageLower = message.toLowerCase()

    // Weather keywords
    if (messageLower.includes('météo') || messageLower.includes('pluie') || messageLower.includes('vent') ||
        messageLower.includes('température') || messageLower.includes('prévision')) {
      return agents.weather
    }

    // Crop health keywords
    if (messageLower.includes('maladie') || messageLower.includes('ravageur') || messageLower.includes('tache') ||
        messageLower.includes('symptôme') || messageLower.includes('diagnostic') || messageLower.includes('traitement')) {
      return agents.crop_health
    }

    // Regulatory keywords
    if (messageLower.includes('amm') || messageLower.includes('réglementation') || messageLower.includes('conformité') ||
        messageLower.includes('autorisation') || messageLower.includes('znt')) {
      return agents.regulatory
    }

    // Planning keywords
    if (messageLower.includes('planification') || messageLower.includes('calendrier') || messageLower.includes('programme') ||
        messageLower.includes('organisation') || messageLower.includes('planning')) {
      return agents.planning
    }

    // Sustainability keywords
    if (messageLower.includes('durabilité') || messageLower.includes('environnement') || messageLower.includes('carbone') ||
        messageLower.includes('biodiversité') || messageLower.includes('bio')) {
      return agents.sustainability
    }

    // Farm data keywords (default)
    return agents.farm_data
  }

  const handleSendMessage = async () => {
    if (!inputValue.trim() || isLoading) return

    const userMessage: Message = {
      id: Date.now().toString(),
      content: inputValue.trim(),
      sender: 'user',
      timestamp: new Date()
    }

    // Select appropriate agent
    const selectedAgent = selectAgentForMessage(inputValue)

    setMessages(prev => [...prev, userMessage])
    setInputValue('')
    setIsLoading(true)
    setIsStreaming(true)

    try {
      // Send message via WebSocket
      webSocket.sendMessage(userMessage.content, selectedAgent.type)
    } catch (error) {
      console.error('Error sending message:', error)

      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: 'Erreur de connexion. Vérifiez votre connexion internet.',
        sender: 'assistant',
        timestamp: new Date(),
        agent: 'error'
      }

      setMessages(prev => [...prev, errorMessage])
      setIsLoading(false)
      setIsStreaming(false)
    }
  }

  const handleVoiceMessage = (message: string) => {
    setInputValue(message)
    // Auto-send voice messages
    setTimeout(() => {
      if (message.trim()) {
        handleSendMessage()
      }
    }, 100)
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  const toggleVoiceInterface = () => {
    setShowVoiceInterface(!showVoiceInterface)
  }

  return (
    <div className="flex flex-col h-full bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-xl font-semibold text-gray-900">Ekumen Assistant</h1>
            <p className="text-sm text-gray-600">
              {currentAgent ? (
                <span className="flex items-center gap-2">
                  <span>{currentAgent.icon}</span>
                  <span>{currentAgent.name} • {currentAgent.description}</span>
                </span>
              ) : (
                'Posez votre question, je sélectionnerai l\'expert approprié'
              )}
            </p>
          </div>
          {isStreaming && (
            <div className="flex items-center gap-2 text-green-600">
              <Loader2 className="h-4 w-4 animate-spin" />
              <span className="text-sm">En cours...</span>
            </div>
          )}
        </div>
      </div>
      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
        {messages.length === 0 ? (
          <div className="text-center py-12">
            <Bot className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">Bienvenue sur Ekumen Assistant</h3>
            <p className="text-gray-600 mb-6">
              Posez vos questions agricoles, je sélectionnerai automatiquement l'expert le plus approprié.
            </p>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-3 max-w-2xl mx-auto">
              {Object.values(agents).map((agent) => (
                <div key={agent.type} className="bg-white rounded-lg p-3 border border-gray-200 text-center">
                  <div className="text-2xl mb-1">{agent.icon}</div>
                  <div className="text-sm font-medium text-gray-900">{agent.name}</div>
                  <div className="text-xs text-gray-600">{agent.description}</div>
                </div>
              ))}
            </div>
          </div>
        ) : (
          messages.map((message) => (
            <div key={message.id} className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`flex max-w-xs lg:max-w-md xl:max-w-lg ${message.sender === 'user' ? 'flex-row-reverse' : 'flex-row'} gap-3`}>
                {/* Avatar */}
                <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
                  message.sender === 'user'
                    ? 'bg-green-600 text-white'
                    : 'bg-gray-200 text-gray-600'
                }`}>
                  {message.sender === 'user' ? (
                    <User className="h-4 w-4" />
                  ) : (
                    <Bot className="h-4 w-4" />
                  )}
                </div>

                {/* Message Content */}
                <div className={`rounded-lg px-4 py-2 ${
                  message.sender === 'user'
                    ? 'bg-green-600 text-white'
                    : 'bg-white border border-gray-200 text-gray-900'
                }`}>
                  {message.sender === 'assistant' && message.agentName && (
                    <div className="text-xs text-gray-500 mb-1 flex items-center gap-1">
                      {agents[message.agent || '']?.icon}
                      <span>{message.agentName}</span>
                    </div>
                  )}
                  <div className="text-sm whitespace-pre-wrap">
                    {message.content}
                    {message.isStreaming && (
                      <span className="inline-block w-2 h-4 bg-gray-400 ml-1 animate-pulse" />
                    )}
                  </div>
                  <div className="text-xs opacity-70 mt-1">
                    {message.timestamp.toLocaleTimeString('fr-FR', {
                      hour: '2-digit',
                      minute: '2-digit'
                    })}
                  </div>
                </div>
              </div>
            </div>
          ))
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="bg-white border-t border-gray-200 px-6 py-4">
        <div className="flex items-end gap-3">
          {/* Voice Interface Toggle */}
          <button
            onClick={toggleVoiceInterface}
            className={`flex-shrink-0 p-2 rounded-full transition-colors ${
              showVoiceInterface
                ? 'bg-green-600 text-white'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
            disabled={isLoading}
            title="Interface vocale"
          >
            <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 24 24">
              <path d="M12 2C13.1 2 14 2.9 14 4V10C14 11.1 13.1 12 12 12S10 11.1 10 10V4C10 2.9 10.9 2 12 2M19 10V12C19 15.9 15.9 19 12 19S5 15.9 5 12V10H7V12C7 14.8 9.2 17 12 17S17 14.8 17 12V10H19Z"/>
            </svg>
          </button>

          {/* Text Input */}
          <div className="flex-1 relative">
            <textarea
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Posez votre question agricole..."
              className="w-full px-4 py-2 border border-gray-300 rounded-lg resize-none focus:ring-2 focus:ring-green-500 focus:border-transparent"
              rows={1}
              disabled={isLoading}
            />
          </div>

          {/* Send Button */}
          <button
            onClick={handleSendMessage}
            disabled={!inputValue.trim() || isLoading}
            className="flex-shrink-0 p-2 bg-green-600 text-white rounded-full hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isLoading ? (
              <Loader2 className="h-5 w-5 animate-spin" />
            ) : (
              <Send className="h-5 w-5" />
            )}
          </button>
        </div>

        {/* Agent Selection Indicator */}
        {inputValue.trim() && !isLoading && (
          <div className="mt-2 text-xs text-gray-600 flex items-center gap-2">
            <span>Agent suggéré:</span>
            {(() => {
              const suggestedAgent = selectAgentForMessage(inputValue)
              return (
                <span className="flex items-center gap-1 bg-gray-100 px-2 py-1 rounded">
                  <span>{suggestedAgent.icon}</span>
                  <span>{suggestedAgent.name}</span>
                </span>
              )
            })()}
          </div>
        )}
      </div>

      {/* Voice Interface Modal */}
      {showVoiceInterface && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold">Interface Vocale</h3>
              <button
                onClick={toggleVoiceInterface}
                className="text-gray-400 hover:text-gray-600"
              >
                <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <VoiceInterface
              onTranscript={(text) => setInputValue(text)}
              onVoiceMessage={handleVoiceMessage}
              className="py-4"
            />
          </div>
        </div>
      )}
    </div>
  )
}

export default ChatInterface
