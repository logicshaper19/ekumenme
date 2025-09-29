import React, { useState, useEffect, useRef } from 'react'
import { Send, Bot, User, Loader2 } from 'lucide-react'
import { useWebSocket } from '../services/websocket'
import { useAuth } from '../hooks/useAuth'
import VoiceInterface from '../components/VoiceInterface'
import MarkdownRenderer from '../components/MarkdownRenderer'

interface Message {
  id: string
  content: string
  sender: 'user' | 'assistant'
  timestamp: Date
  agent?: string
  agentName?: string
  isStreaming?: boolean
  metadata?: {
    agent_type?: string
    confidence?: number
    recommendations?: any[]
    [key: string]: any
  }
}

interface AgentInfo {
  type: string
  name: string
  icon: string
  description: string
}

const ChatInterface: React.FC = () => {
  const { isAuthenticated } = useAuth()
  const [messages, setMessages] = useState<Message[]>([])
  const [inputValue, setInputValue] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [currentAgent, setCurrentAgent] = useState<AgentInfo | null>(null)
  const [isStreaming, setIsStreaming] = useState(false)
  const [showVoiceInterface, setShowVoiceInterface] = useState(false)
  const [conversationId, setConversationId] = useState<string | null>(null)
  const [isCreatingConversation, setIsCreatingConversation] = useState(false)
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

  // Function to create a new conversation
  const createConversation = async (): Promise<string | null> => {
    try {
      setIsCreatingConversation(true)
      const token = localStorage.getItem('auth_token')

      if (!token) {
        console.error('No auth token found')
        return null
      }

      const response = await fetch('/api/v1/chat/conversations', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          agent_type: 'farm_data',
          title: 'Nouvelle conversation'
        })
      })

      if (!response.ok) {
        throw new Error(`Failed to create conversation: ${response.statusText}`)
      }

      const data = await response.json()
      console.log('Conversation created:', data.id)
      return data.id
    } catch (error) {
      console.error('Error creating conversation:', error)
      return null
    } finally {
      setIsCreatingConversation(false)
    }
  }

  // Initialize conversation only once when component mounts and user is authenticated
  useEffect(() => {
    let mounted = true

    if (!isAuthenticated) {
      return
    }

    // Only create conversation if we don't have one and aren't already creating one
    if (!conversationId && !isCreatingConversation) {
      const initializeChat = async () => {
        if (!mounted) return

        console.log('Initializing chat conversation...')
        const newConversationId = await createConversation()
        if (!newConversationId || !mounted) {
          console.error('Failed to create conversation')
          return
        }

        if (mounted) {
          setConversationId(newConversationId)
          console.log('Connecting to conversation:', newConversationId)

          // Wait a bit for the conversation to be fully created before connecting
          setTimeout(() => {
            if (mounted) {
              webSocket.joinConversation(newConversationId)
            }
          }, 100)
        }
      }

      initializeChat()
    }

    return () => {
      mounted = false
    }
  }, []) // Empty dependency array - run once only

  // Set up WebSocket event listeners (separate effect)
  useEffect(() => {
    if (!isAuthenticated) {
      return
    }

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
        content: '🌾 Traitement en cours...',
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

    // Handle workflow completion with final response
    webSocket.onStreamingComplete((data) => {
      console.log('Received streaming complete:', data)
      setMessages(prev => {
        // First try to find streaming assistant message by message_id
        let streamingMessage = data.message_id
          ? prev.find(msg => msg.id === data.message_id && msg.isStreaming && msg.sender === 'assistant')
          : null

        // If not found by message_id, try to find any streaming assistant message
        if (!streamingMessage) {
          streamingMessage = prev.find(msg => msg.isStreaming && msg.sender === 'assistant')
        }

        if (streamingMessage) {
          // Update the existing streaming message
          return prev.map(msg =>
            msg.id === streamingMessage.id
              ? {
                  ...msg,
                  content: data.message,
                  isStreaming: false,
                  metadata: {
                    agent_type: data.agent_type,
                    confidence: data.confidence,
                    recommendations: data.recommendations,
                    thread_id: data.thread_id,
                    ...data.metadata
                  }
                }
              : msg
          )
        } else {
          // No streaming message found, create a new assistant message
          const newMessage: Message = {
            id: data.message_id || `response-${Date.now()}`,
            content: data.message,
            sender: 'assistant',
            timestamp: new Date(),
            isStreaming: false,
            metadata: {
              agent_type: data.agent_type,
              confidence: data.confidence,
              recommendations: data.recommendations,
              thread_id: data.thread_id,
              ...data.metadata
            }
          }
          return [...prev, newMessage]
        }
      })
      setIsLoading(false)
      setIsStreaming(false)
    })

    // Handle workflow status updates
    webSocket.onWorkflowStart((data) => {
      console.log('Workflow started:', data.message)

      // Check if there's already a streaming assistant message
      setMessages(prev => {
        const hasStreamingMessage = prev.some(msg => msg.sender === 'assistant' && msg.isStreaming)

        if (hasStreamingMessage) {
          // Update existing streaming message
          return prev.map(msg =>
            msg.sender === 'assistant' && msg.isStreaming
              ? { ...msg, content: data.message }
              : msg
          )
        } else {
          // Create new streaming assistant message
          const newMessage: Message = {
            id: data.message_id || `workflow-${Date.now()}`,
            content: data.message,
            sender: 'assistant',
            timestamp: new Date(),
            isStreaming: true
          }
          return [...prev, newMessage]
        }
      })
    })

    webSocket.onWorkflowInit((data) => {
      console.log('Workflow initialized:', data.message)
      // Update the existing assistant message with initialization status
      setMessages(prev => prev.map(msg =>
        msg.sender === 'assistant' && msg.isStreaming
          ? { ...msg, content: data.message }
          : msg
      ))
    })

    webSocket.onWorkflowStep((data) => {
      console.log('Workflow step:', data.step, data.message)
      // Update the existing assistant message with step progress
      setMessages(prev => prev.map(msg =>
        msg.sender === 'assistant' && msg.isStreaming
          ? { ...msg, content: data.message }
          : msg
      ))
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
      webSocket.off('chat:streaming_complete')
      webSocket.off('chat:workflow_start')
      webSocket.off('chat:workflow_init')
      webSocket.off('chat:workflow_step')
      webSocket.off('chat:agent_selected')
      webSocket.off('error')
    }
  }, [isAuthenticated])

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
    if (!inputValue.trim() || isLoading || !conversationId) return

    const threadId = `thread-${Date.now()}`
    const messageId = `msg-${Date.now()}`
    const userMessage: Message = {
      id: messageId,
      content: inputValue.trim(),
      sender: 'user',
      timestamp: new Date(),
      metadata: { thread_id: threadId }
    }

    // Select appropriate agent
    const selectedAgent = selectAgentForMessage(inputValue)

    setMessages(prev => [...prev, userMessage])
    setInputValue('')
    setIsLoading(true)
    setIsStreaming(true)

    try {
      // Send message via WebSocket with thread ID
      await webSocket.sendMessage(userMessage.content, selectedAgent.type, messageId, threadId)
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

  // Show loading state while creating conversation or if no conversation ID yet
  if (isCreatingConversation || (!conversationId && isAuthenticated)) {
    return (
      <div className="flex flex-col h-full bg-gray-50 items-center justify-center">
        <div className="text-center">
          <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4 text-green-600" />
          <p className="text-gray-600">Initialisation de la conversation...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-8 py-4">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
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
      <div className="flex-1 overflow-y-auto px-8 py-6">
        <div className="max-w-4xl mx-auto space-y-6">
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
                <div className={`flex max-w-2xl ${message.sender === 'user' ? 'flex-row-reverse' : 'flex-row'} gap-3`}>
                  {/* Avatar */}
                  <div className={`flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center ${
                    message.sender === 'user'
                      ? 'bg-green-600 text-white'
                      : 'bg-gray-200 text-gray-600'
                  }`}>
                    {message.sender === 'user' ? (
                      <User className="h-5 w-5" />
                    ) : (
                      <Bot className="h-5 w-5" />
                    )}
                  </div>

                  {/* Message Content */}
                  <div className={`rounded-lg px-4 py-3 ${
                    message.sender === 'user'
                      ? 'bg-green-600 text-white'
                      : 'bg-white border border-gray-200 text-gray-900 shadow-sm'
                  }`}>
                    {message.sender === 'assistant' && message.agentName && (
                      <div className="text-xs text-gray-500 mb-2 flex items-center gap-1">
                        {agents[message.agent || '']?.icon}
                        <span>{message.agentName}</span>
                      </div>
                    )}
                    <div className="text-base leading-relaxed">
                      {message.sender === 'assistant' ? (
                        <MarkdownRenderer content={message.content} />
                      ) : (
                        <div className="whitespace-pre-wrap">{message.content}</div>
                      )}
                      {message.isStreaming && (
                        <span className="inline-block w-2 h-5 bg-gray-400 ml-1 animate-pulse" />
                      )}
                    </div>
                    <div className="text-xs opacity-70 mt-2">
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
      </div>

      {/* Input Area - At the bottom like normal chat */}
      <div className="bg-white border-t border-gray-200 px-8 py-4">
        <div className="max-w-4xl mx-auto">
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
                className="w-full px-4 py-3 border border-gray-300 rounded-lg resize-none focus:ring-2 focus:ring-green-500 focus:border-transparent text-base"
                rows={1}
                disabled={isLoading}
              />
            </div>

            {/* Send Button */}
            <button
              onClick={handleSendMessage}
              disabled={!inputValue.trim() || isLoading}
              className="flex-shrink-0 p-3 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
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
            <div className="mt-3 text-sm text-gray-600 flex items-center gap-2">
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
