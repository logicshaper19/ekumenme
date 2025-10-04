import React, { useState, useEffect, useRef } from 'react'
import { Send, Bot, User, Loader2, Paperclip, X, FileText, Globe, Package } from 'lucide-react'
import { useSearchParams } from 'react-router-dom'
import { useWebSocket } from '../services/websocket'
import { useAuth } from '../hooks/useAuth'
import VoiceInterface from '../components/VoiceInterface'
import MarkdownRenderer from '../components/MarkdownRenderer'
import MessageActions from '../components/MessageActions'
import Sources from '../components/Sources'

type ChatMode = 'supplier' | 'internet' | null

interface AttachedFile {
  id: string
  name: string
  size: number
  type: string
  file: File
}

interface Source {
  title: string
  url: string
  snippet?: string
  relevance?: number
  type?: 'web' | 'database' | 'document' | 'api'
}

interface Message {
  id: string
  content: string
  sender: 'user' | 'assistant'
  timestamp: Date
  agent?: string
  agentName?: string
  isStreaming?: boolean
  queryText?: string  // The user's original query (for assistant messages)
  attachments?: AttachedFile[]
  mode?: ChatMode
  sources?: Source[]  // Sources used to generate the response
  metadata?: {
    agent_type?: string
    confidence?: number
    recommendations?: any[]
    [key: string]: any
  }
}


const ChatInterface: React.FC = () => {
  const { isAuthenticated } = useAuth()
  const [searchParams] = useSearchParams()
  const [messages, setMessages] = useState<Message[]>([])
  const [inputValue, setInputValue] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [isStreaming, setIsStreaming] = useState(false)
  const [showVoiceInterface, setShowVoiceInterface] = useState(false)
  const [conversationId, setConversationId] = useState<string | null>(null)
  const [isLoadingConversation, setIsLoadingConversation] = useState(false)
  const [isCreatingConversation, setIsCreatingConversation] = useState(false)
  const [chatMode, setChatMode] = useState<ChatMode>(null)
  const [attachedFiles, setAttachedFiles] = useState<AttachedFile[]>([])
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const lastUserQueryRef = useRef<string>('')  // Track last user query for feedback
  const fileInputRef = useRef<HTMLInputElement>(null)
  const webSocket = useWebSocket()


  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  // Load conversation from URL parameter
  useEffect(() => {
    const conversationParam = searchParams.get('conversation')
    if (conversationParam) {
      loadConversation(conversationParam)
    }
  }, [searchParams])

  // Function to load an existing conversation
  const loadConversation = async (conversationId: string) => {
    try {
      setIsLoadingConversation(true)
      const token = localStorage.getItem('auth_token')

      if (!token) {
        console.error('No auth token found')
        return
      }

      // Get conversation details
      const conversationResponse = await fetch(`/api/v1/chat/conversations/${conversationId}`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })

      if (!conversationResponse.ok) {
        throw new Error(`Failed to load conversation: ${conversationResponse.statusText}`)
      }

      const conversation = await conversationResponse.json()
      
      // Set the conversation ID
      setConversationId(conversationId)

      // Load conversation messages
      const messagesResponse = await fetch(`/api/v1/chat/conversations/${conversationId}/messages`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })

      if (messagesResponse.ok) {
        const messagesData = await messagesResponse.json()
        // Convert backend messages to frontend format
        const formattedMessages: Message[] = messagesData.map((msg: any) => ({
          id: msg.id,
          content: msg.content,
          sender: msg.sender === 'user' ? 'user' : 'agent',
          timestamp: new Date(msg.created_at),
          agentType: msg.agent_type,
          sources: msg.sources || [],
          metadata: msg.metadata || {}
        }))
        setMessages(formattedMessages)
      }

    } catch (error) {
      console.error('Error loading conversation:', error)
      // If conversation doesn't exist, create a new one
      const newConversationId = await createConversation()
      if (newConversationId) {
        setConversationId(newConversationId)
      }
    } finally {
      setIsLoadingConversation(false)
    }
  }

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

  // Set up WebSocket event listeners (run when authentication changes)
  useEffect(() => {
    if (!isAuthenticated) {
      console.log('⏭️ Skipping WebSocket listener setup - not authenticated')
      return
    }

    console.log('🔧 Setting up WebSocket event listeners')

    // Define all handlers with stable references
    // Using functional state updates ensures we don't need dependencies
    const handleMessageResponse = (data: any) => {
      const assistantMessage: Message = {
        id: data.message.id,
        content: data.message.content,
        sender: 'assistant',
        timestamp: new Date(data.message.timestamp),
        queryText: lastUserQueryRef.current
      }

      setMessages(prev => [...prev, assistantMessage])
      setIsLoading(false)
      setIsStreaming(false)
    }

    const handleStreamingStart = (data: any) => {
      const assistantMessage: Message = {
        id: data.message_id,
        content: '🌾 Traitement en cours...',
        sender: 'assistant',
        timestamp: new Date(),
        isStreaming: true,
        queryText: lastUserQueryRef.current
      }

      setMessages(prev => [...prev, assistantMessage])
    }

    const handleStreamingChunk = (data: any) => {
      console.log('📦 Received streaming chunk:', data)

      setMessages(prev => prev.map(msg => {
        if (msg.id === data.message_id) {
          // If this is the first chunk, replace the placeholder
          const isFirstChunk = msg.content === '🌾 Traitement en cours...'
          const newContent = isFirstChunk ? data.chunk : msg.content + data.chunk
          console.log(`📝 Updating message ${msg.id}: isFirstChunk=${isFirstChunk}, chunk="${data.chunk}", newContent="${newContent.substring(0, 50)}..."`)
          return {
            ...msg,
            content: newContent
          }
        }
        return msg
      }))

      if (data.is_complete) {
        setMessages(prev => prev.map(msg =>
          msg.id === data.message_id
            ? { ...msg, isStreaming: false }
            : msg
        ))
        setIsLoading(false)
        setIsStreaming(false)
      }
    }

    // Handle completion (unified 'done' or legacy 'workflow_result')
    const handleStreamingComplete = (data: any) => {
      console.log('Received streaming complete:', data)
      setMessages(prev => {
        // Find existing streaming assistant message (by ID or just any streaming message)
        let streamingMessage = prev.find(msg => msg.isStreaming && msg.sender === 'assistant')

        if (streamingMessage) {
          // Update existing message: mark complete, update ID to DB ID, and attach sources/metadata
          return prev.map(msg =>
            msg.id === streamingMessage!.id
              ? {
                  ...msg,
                  id: data.message_id || msg.id, // Update to real DB message ID
                  // If backend included a final message for legacy path, prefer it; otherwise keep accumulated content
                  content: (data as any).message ?? msg.content,
                  isStreaming: false,
                  sources: data.sources || msg.sources || [],
                  metadata: {
                    ...(msg.metadata || {}),
                    // Keep legacy fields if provided; otherwise leave existing metadata
                    agent_type: (data as any).agent_type ?? msg.metadata?.agent_type,
                    confidence: (data as any).confidence ?? msg.metadata?.confidence,
                    recommendations: (data as any).recommendations ?? msg.metadata?.recommendations,
                    thread_id: (data as any).thread_id ?? msg.metadata?.thread_id,
                    ...(data as any).metadata
                  }
                }
              : msg
          )
        } else {
          // No streaming message found, create a new assistant message (fallback)
          const newMessage: Message = {
            id: data.message_id || `response-${Date.now()}`,
            content: (data as any).message || '',
            sender: 'assistant',
            timestamp: new Date(),
            isStreaming: false,
            sources: data.sources || [],
            metadata: {
              agent_type: (data as any).agent_type,
              confidence: (data as any).confidence,
              recommendations: (data as any).recommendations,
              thread_id: (data as any).thread_id,
              ...(data as any).metadata
            }
          }
          return [...prev, newMessage]
        }
      })
      setIsLoading(false)
      setIsStreaming(false)
    }

    // Handle workflow status updates
    const handleWorkflowStart = (data: any) => {
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
    }

    const handleWorkflowInit = (data: any) => {
      console.log('Workflow initialized:', data.message)
      // Update the existing assistant message with initialization status
      setMessages(prev => prev.map(msg =>
        msg.sender === 'assistant' && msg.isStreaming
          ? { ...msg, content: data.message }
          : msg
      ))
    }

    const handleWorkflowStep = (data: any) => {
      console.log('Workflow step:', data.step, data.message)
      // Update the existing assistant message with step progress
      setMessages(prev => prev.map(msg =>
        msg.sender === 'assistant' && msg.isStreaming
          ? { ...msg, content: data.message }
          : msg
      ))
    }


    const handleError = (data: any) => {
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
    }

    // Register all handlers
    webSocket.onMessageResponse(handleMessageResponse)
    webSocket.onStreamingStart(handleStreamingStart)
    webSocket.onStreamingChunk(handleStreamingChunk)
    webSocket.onStreamingComplete(handleStreamingComplete)
    webSocket.onWorkflowStart(handleWorkflowStart)
    webSocket.onWorkflowInit(handleWorkflowInit)
    webSocket.onWorkflowStep(handleWorkflowStep)
    webSocket.onError(handleError)

    return () => {
      console.log('🧹 Cleaning up WebSocket event listeners')
      webSocket.off('chat:message_response', handleMessageResponse)
      webSocket.off('chat:streaming_start', handleStreamingStart)
      webSocket.off('chat:streaming_chunk', handleStreamingChunk)
      webSocket.off('chat:streaming_complete', handleStreamingComplete)
      webSocket.off('chat:workflow_start', handleWorkflowStart)
      webSocket.off('chat:workflow_init', handleWorkflowInit)
      webSocket.off('chat:workflow_step', handleWorkflowStep)
      webSocket.off('error', handleError)
    }
  }, [isAuthenticated]) // Re-run only when authentication status changes


  // File handling functions
  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files
    if (!files) return

    const newFiles: AttachedFile[] = Array.from(files).map(file => ({
      id: `file-${Date.now()}-${Math.random()}`,
      name: file.name,
      size: file.size,
      type: file.type,
      file: file
    }))

    setAttachedFiles(prev => [...prev, ...newFiles])
  }

  const handleRemoveFile = (fileId: string) => {
    setAttachedFiles(prev => prev.filter(f => f.id !== fileId))
  }

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return bytes + ' B'
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
  }

  const handleSendMessage = async () => {
    if (!inputValue.trim() || isLoading || !conversationId) return

    const threadId = `thread-${Date.now()}`
    const messageId = `msg-${Date.now()}`
    const queryText = inputValue.trim()
    const userMessage: Message = {
      id: messageId,
      content: queryText,
      sender: 'user',
      timestamp: new Date(),
      attachments: attachedFiles.length > 0 ? [...attachedFiles] : undefined,
      mode: chatMode,
      metadata: { thread_id: threadId }
    }

    // Store the query for feedback tracking
    lastUserQueryRef.current = queryText

    setMessages(prev => [...prev, userMessage])
    setInputValue('')
    setAttachedFiles([])  // Clear attachments after sending
    setIsLoading(true)
    setIsStreaming(true)

    try {
      // Send message via WebSocket with thread ID and mode
      // No agent_type needed - LangChain handles routing intelligently
      console.log('🚀 Sending message with chatMode:', chatMode)
      await webSocket.sendMessage(userMessage.content, null, messageId, threadId, chatMode)
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
      <div
        className="flex flex-col h-full items-center justify-center"
        style={{
          backgroundColor: 'var(--bg-app)',
          color: 'var(--text-primary)'
        }}
      >
        <div className="text-center">
          <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4" style={{ color: 'var(--brand-600)' }} />
          <p style={{ color: 'var(--text-secondary)' }}>Initialisation de la conversation...</p>
        </div>
      </div>
    )
  }

  return (
    <div
      className="flex flex-col h-full"
      style={{
        backgroundColor: 'var(--bg-app)',
        color: 'var(--text-primary)',
        transition: 'var(--transition-theme)'
      }}
    >
      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto px-8 py-6">
        <div className="max-w-4xl mx-auto space-y-6">
          {messages.length === 0 ? (
            <div className="text-center py-12">
              <Bot className="h-12 w-12 mx-auto mb-4" style={{ color: 'var(--text-muted)' }} />
              <h3 className="text-lg font-medium text-primary mb-2">Bienvenue sur Ekumen Assistant</h3>
              <p className="text-secondary mb-6">
                Posez vos questions agricoles, je sélectionnerai automatiquement l'expert le plus approprié.
              </p>
            </div>
          ) : (
            messages.map((message) => (
              <div key={message.id} className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`flex max-w-2xl ${message.sender === 'user' ? 'flex-row-reverse' : 'flex-row'} gap-3`}>
                  {/* Avatar */}
                  <div
                    className="flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center"
                    style={{
                      backgroundColor: message.sender === 'user' ? 'var(--brand-600)' : 'var(--bg-input)',
                      color: message.sender === 'user' ? 'var(--text-inverse)' : 'var(--text-secondary)'
                    }}
                  >
                    {message.sender === 'user' ? (
                      <User className="h-5 w-5" />
                    ) : (
                      <Bot className="h-5 w-5" />
                    )}
                  </div>

                  {/* Message Content */}
                  <div
                    className="rounded-lg px-4 py-3"
                    style={{
                      backgroundColor: message.sender === 'user' ? 'var(--brand-600)' : 'var(--bg-card)',
                      color: message.sender === 'user' ? 'var(--text-inverse)' : 'var(--text-primary)',
                      borderColor: message.sender === 'user' ? 'transparent' : 'var(--border-subtle)',
                      borderWidth: message.sender === 'user' ? '0' : '1px',
                      boxShadow: message.sender === 'user' ? 'none' : 'var(--shadow-sm)'
                    }}
                  >

                    {/* Mode Badge for User Messages */}
                    {message.sender === 'user' && message.mode && (
                      <div className="mb-2 flex items-center gap-1 text-xs opacity-80">
                        {message.mode === 'supplier' ? (
                          <>
                            <Package className="h-3 w-3" />
                            <span>Mode Fournisseurs</span>
                          </>
                        ) : (
                          <>
                            <Globe className="h-3 w-3" />
                            <span>Internet</span>
                          </>
                        )}
                      </div>
                    )}

                    <div className="text-base leading-relaxed">
                      {message.sender === 'assistant' ? (
                        <MarkdownRenderer content={message.content} />
                      ) : (
                        <div className="whitespace-pre-wrap">{message.content}</div>
                      )}
                      {message.isStreaming && (
                        <span
                          className="inline-block w-2 h-5 ml-1 animate-pulse"
                          style={{ backgroundColor: 'var(--text-muted)' }}
                        />
                      )}
                    </div>

                    {/* Sources for Assistant Messages */}
                    {message.sender === 'assistant' && message.sources && message.sources.length > 0 && (
                      <Sources sources={message.sources} />
                    )}

                    {/* Attachments for User Messages */}
                    {message.sender === 'user' && message.attachments && message.attachments.length > 0 && (
                      <div className="mt-2 flex flex-wrap gap-2">
                        {message.attachments.map(file => (
                          <div
                            key={file.id}
                            className="flex items-center gap-1 px-2 py-1 rounded text-xs"
                            style={{
                              backgroundColor: 'rgba(255, 255, 255, 0.2)',
                              color: 'var(--text-inverse)'
                            }}
                          >
                            <FileText className="h-3 w-3" />
                            <span>{file.name}</span>
                          </div>
                        ))}
                      </div>
                    )}

                    <div className="text-xs opacity-70 mt-2">
                      {message.timestamp.toLocaleTimeString('fr-FR', {
                        hour: '2-digit',
                        minute: '2-digit'
                      })}
                    </div>

                    {/* Message Actions (thumbs up/down, copy) - only for assistant messages */}
                    {message.sender === 'assistant' && !message.isStreaming && conversationId && (
                      <MessageActions
                        messageId={message.id}
                        conversationId={conversationId}
                        content={message.content}
                        queryText={message.queryText}
                      />
                    )}
                  </div>
                </div>
              </div>
            ))
          )}
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input Area - Clean ChatGPT-like Interface */}
      <div
        className="px-8 py-4 border-t"
        style={{
          backgroundColor: 'var(--bg-card)',
          borderColor: 'var(--border-subtle)'
        }}
      >
        <div className="max-w-4xl mx-auto">
          {/* Attached Files Display */}
          {attachedFiles.length > 0 && (
            <div className="mb-3 flex flex-wrap gap-2">
              {attachedFiles.map(file => (
                <div
                  key={file.id}
                  className="flex items-center gap-2 px-3 py-2 rounded-lg text-sm"
                  style={{ backgroundColor: 'var(--bg-input)' }}
                >
                  <FileText className="h-4 w-4" style={{ color: 'var(--text-secondary)' }} />
                  <span className="text-primary">{file.name}</span>
                  <span className="text-muted">({formatFileSize(file.size)})</span>
                  <button
                    onClick={() => handleRemoveFile(file.id)}
                    className="ml-1"
                    style={{ color: 'var(--text-muted)' }}
                  >
                    <X className="h-4 w-4 hover:text-error" />
                  </button>
                </div>
              ))}
            </div>
          )}

          {/* Main Input Card - Clean Design */}
          <div
            className="rounded-2xl border shadow-lg"
            style={{
              backgroundColor: 'var(--bg-input)',
              borderColor: 'var(--border-default)'
            }}
          >
            {/* Input Area */}
            <div className="relative">
              <textarea
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Posez votre question agricole..."
                className="w-full bg-transparent px-6 py-8 text-lg rounded-t-2xl focus:outline-none transition-colors resize-none"
                style={{
                  color: 'var(--text-primary)',
                  minHeight: '120px'
                }}
                onFocus={(e) => {
                  e.currentTarget.parentElement!.parentElement!.style.borderColor = 'var(--brand-600)'
                }}
                onBlur={(e) => {
                  e.currentTarget.parentElement!.parentElement!.style.borderColor = 'var(--border-default)'
                }}
                disabled={isLoading}
              />
            </div>

            {/* All Buttons at Bottom of Card */}
            <div
              className="flex items-center justify-between px-6 py-4 border-t"
              style={{ borderColor: 'var(--border-subtle)' }}
            >
              {/* Mode Buttons - Left Side */}
              <div className="flex items-center gap-3">
                <button
                  onClick={() => setChatMode(chatMode === 'supplier' ? null : 'supplier')}
                  className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm transition-colors border ${
                    chatMode === 'supplier'
                      ? 'bg-blue-100 text-blue-700 border-blue-300'
                      : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                  }`}
                  disabled={isLoading}
                >
                  <Package className="h-4 w-4" />
                  <span>Mode Fournisseurs</span>
                </button>
                <button
                  onClick={() => setChatMode(chatMode === 'internet' ? null : 'internet')}
                  className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm transition-colors border ${
                    chatMode === 'internet'
                      ? 'bg-blue-100 text-blue-700 border-blue-300'
                      : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                  }`}
                  disabled={isLoading}
                >
                  <Globe className="h-4 w-4" />
                  <span>Internet</span>
                </button>
              </div>

              {/* Action Buttons - Right Side */}
              <div className="flex items-center gap-3">
                {/* File Attachment Button */}
                <input
                  ref={fileInputRef}
                  type="file"
                  multiple
                  onChange={handleFileSelect}
                  className="hidden"
                  accept=".pdf,.doc,.docx,.txt,.jpg,.jpeg,.png,.csv,.xlsx"
                />
                <button
                  onClick={() => fileInputRef.current?.click()}
                  className="flex items-center justify-center p-2 rounded-lg transition-colors border"
                  style={{
                    backgroundColor: 'var(--bg-card)',
                    color: 'var(--text-secondary)',
                    borderColor: 'var(--border-default)'
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.backgroundColor = 'var(--bg-card-hover)'
                    e.currentTarget.style.color = 'var(--text-primary)'
                    e.currentTarget.style.borderColor = 'var(--border-subtle)'
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.backgroundColor = 'var(--bg-card)'
                    e.currentTarget.style.color = 'var(--text-secondary)'
                    e.currentTarget.style.borderColor = 'var(--border-default)'
                  }}
                  disabled={isLoading}
                  title="Attach files"
                >
                  <Paperclip className="h-4 w-4" />
                </button>
                <button
                  onClick={toggleVoiceInterface}
                  className={`flex items-center justify-center p-2 rounded-lg transition-colors border ${
                    showVoiceInterface
                      ? 'bg-green-100 text-green-700 border-green-300'
                      : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                  }`}
                  disabled={isLoading}
                  title="Voice interface"
                >
                  <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M12 2C13.1 2 14 2.9 14 4V10C14 11.1 13.1 12 12 12S10 11.1 10 10V4C10 2.9 10.9 2 12 2M19 10V12C19 15.9 15.9 19 12 19S5 15.9 5 12V10H7V12C7 14.8 9.2 17 12 17S17 14.8 17 12V10H19Z"/>
                  </svg>
                </button>
                <button
                  onClick={handleSendMessage}
                  disabled={!inputValue.trim() || isLoading}
                  className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm transition-colors border disabled:opacity-50 disabled:cursor-not-allowed"
                  style={{
                    backgroundColor: 'var(--brand-600)',
                    color: 'var(--text-inverse)',
                    borderColor: 'var(--brand-600)'
                  }}
                  onMouseEnter={(e) => {
                    if (!e.currentTarget.disabled) {
                      e.currentTarget.style.backgroundColor = 'var(--brand-700)'
                      e.currentTarget.style.borderColor = 'var(--brand-700)'
                    }
                  }}
                  onMouseLeave={(e) => {
                    if (!e.currentTarget.disabled) {
                      e.currentTarget.style.backgroundColor = 'var(--brand-600)'
                      e.currentTarget.style.borderColor = 'var(--brand-600)'
                    }
                  }}
                  title="Send message"
                >
                  {isLoading ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Send className="h-4 w-4" />
                  )}
                  <span>Envoyer</span>
                </button>
              </div>
            </div>
          </div>


          {/* Popular Suggestions Below Input */}
          {messages.length === 0 && (
            <div className="text-center mt-8">
              <h3
                className="text-sm mb-4 font-medium"
                style={{ color: 'var(--text-muted)' }}
              >
                Suggestions populaires
              </h3>
              <div className="flex flex-wrap justify-center gap-3">
                <button
                  className="px-4 py-2 rounded-full text-sm transition-colors border"
                    style={{
                    backgroundColor: 'var(--bg-card)',
                    color: 'var(--text-secondary)',
                    borderColor: 'var(--border-default)'
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.backgroundColor = 'var(--bg-card-hover)'
                    e.currentTarget.style.color = 'var(--text-primary)'
                    e.currentTarget.style.borderColor = 'var(--border-subtle)'
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.backgroundColor = 'var(--bg-card)'
                    e.currentTarget.style.color = 'var(--text-secondary)'
                    e.currentTarget.style.borderColor = 'var(--border-default)'
                  }}
                  onClick={() => setInputValue("Quand traiter contre le mildiou ?")}
                >
                  "Quand traiter contre le mildiou ?"
                </button>
                <button
                  className="px-4 py-2 rounded-full text-sm transition-colors border"
                  style={{
                    backgroundColor: 'var(--bg-card)',
                    color: 'var(--text-secondary)',
                    borderColor: 'var(--border-default)'
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.backgroundColor = 'var(--bg-card-hover)'
                    e.currentTarget.style.color = 'var(--text-primary)'
                    e.currentTarget.style.borderColor = 'var(--border-subtle)'
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.backgroundColor = 'var(--bg-card)'
                    e.currentTarget.style.color = 'var(--text-secondary)'
                    e.currentTarget.style.borderColor = 'var(--border-default)'
                  }}
                  onClick={() => setInputValue("Prix des semences 2024")}
                >
                  "Prix des semences 2024"
                </button>
                <button
                  className="px-4 py-2 rounded-full text-sm transition-colors border"
                  style={{
                    backgroundColor: 'var(--bg-card)',
                    color: 'var(--text-secondary)',
                    borderColor: 'var(--border-default)'
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.backgroundColor = 'var(--bg-card-hover)'
                    e.currentTarget.style.color = 'var(--text-primary)'
                    e.currentTarget.style.borderColor = 'var(--border-subtle)'
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.backgroundColor = 'var(--bg-card)'
                    e.currentTarget.style.color = 'var(--text-secondary)'
                    e.currentTarget.style.borderColor = 'var(--border-default)'
                  }}
                  onClick={() => setInputValue("Météo pour les 7 prochains jours")}
                >
                  "Météo pour les 7 prochains jours"
                </button>
                <button
                  className="px-4 py-2 rounded-full text-sm transition-colors border"
                  style={{
                    backgroundColor: 'var(--bg-card)',
                    color: 'var(--text-secondary)',
                    borderColor: 'var(--border-default)'
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.backgroundColor = 'var(--bg-card-hover)'
                    e.currentTarget.style.color = 'var(--text-primary)'
                    e.currentTarget.style.borderColor = 'var(--border-subtle)'
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.backgroundColor = 'var(--bg-card)'
                    e.currentTarget.style.color = 'var(--text-secondary)'
                    e.currentTarget.style.borderColor = 'var(--border-default)'
                  }}
                  onClick={() => setInputValue("Analyse de mes parcelles")}
                >
                  "Analyse de mes parcelles"
                </button>
                <button
                  className="px-4 py-2 rounded-full text-sm transition-colors border"
                  style={{
                    backgroundColor: 'var(--bg-card)',
                    color: 'var(--text-secondary)',
                    borderColor: 'var(--border-default)'
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.backgroundColor = 'var(--bg-card-hover)'
                    e.currentTarget.style.color = 'var(--text-primary)'
                    e.currentTarget.style.borderColor = 'var(--border-subtle)'
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.backgroundColor = 'var(--bg-card)'
                    e.currentTarget.style.color = 'var(--text-secondary)'
                    e.currentTarget.style.borderColor = 'var(--border-default)'
                  }}
                  onClick={() => setInputValue("Fournisseurs locaux")}
                >
                  "Fournisseurs locaux"
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Voice Interface Modal */}
      {showVoiceInterface && (
        <div className="fixed inset-0 flex items-center justify-center z-50" style={{ backgroundColor: 'rgba(0, 0, 0, 0.5)' }}>
          <div
            className="rounded-lg p-6 max-w-md w-full mx-4"
            style={{
              backgroundColor: 'var(--bg-elevated)',
              color: 'var(--text-primary)',
              boxShadow: 'var(--shadow-lg)'
            }}
          >
            <div className="flex justify-between items-center mb-4">
              <h3
                className="text-lg font-semibold"
                style={{ color: 'var(--text-primary)' }}
              >
                Interface Vocale
              </h3>
              <button
                onClick={toggleVoiceInterface}
                style={{ color: 'var(--text-muted)' }}
                onMouseEnter={(e) => e.currentTarget.style.color = 'var(--text-secondary)'}
                onMouseLeave={(e) => e.currentTarget.style.color = 'var(--text-muted)'}
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
