export interface ChatMessage {
  id: string
  content: string
  sender: 'user' | 'assistant'
  timestamp: Date
  agent?: string
  agentName?: string
  isStreaming?: boolean
}

interface WebSocketMessage {
  type: string
  [key: string]: any
}

class WebSocketService {
  private socket: WebSocket | null = null
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private reconnectDelay = 1000
  private eventListeners: Map<string, Function[]> = new Map()
  private conversationId: string | null = null

  constructor() {
    // Don't auto-connect, wait for conversation ID
  }

  private connect(conversationId: string) {
    try {
      // Get auth token from localStorage
      const authToken = localStorage.getItem('auth_token')
      if (!authToken) {
        throw new Error('No authentication token found. Please log in.')
      }

      const wsUrl = import.meta.env.VITE_WS_URL || 'ws://localhost:8000'
      const url = `${wsUrl}/api/v1/chat/ws/${conversationId}?token=${authToken}`

      console.log('Connecting to WebSocket:', url)
      this.socket = new WebSocket(url)
      this.conversationId = conversationId
      this.setupEventListeners()
    } catch (error) {
      console.error('Failed to connect to WebSocket:', error)
      throw error
    }
  }

  private setupEventListeners() {
    if (!this.socket) return

    this.socket.onopen = () => {
      console.log('Connected to WebSocket server')
      this.reconnectAttempts = 0
      this.emit('connect', {})
    }

    this.socket.onclose = (event) => {
      console.log('Disconnected from WebSocket server:', event.reason)
      this.emit('disconnect', { reason: event.reason })
      this.handleReconnect()
    }

    this.socket.onerror = (error) => {
      console.error('WebSocket error:', error)
      this.emit('error', { message: 'WebSocket connection error' })
    }

    this.socket.onmessage = (event) => {
      try {
        const data: WebSocketMessage = JSON.parse(event.data)
        this.handleMessage(data)
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error)
      }
    }
  }

  private handleMessage(data: WebSocketMessage) {
    switch (data.type) {
      case 'connection':
        this.emit('connect', data)
        break

      // Unified streaming events (SSE + WS)
      case 'token': {
        const text = data.text ?? data.token ?? data.content ?? ''
        console.log('🔵 WebSocket received token:', { text, message_id: data.message_id, data })
        if (!text) {
          console.warn('⚠️ Token event with no text:', data)
          return
        }
        this.emit('chat:streaming_chunk', {
          message_id: data.message_id || 'current',
          chunk: text,
          is_complete: false
        })
        break
      }
      case 'done': {
        // Unified completion event
        this.emit('chat:streaming_complete', {
          message_id: data.message_id || 'current',
          sources: data.sources || [],
          citation_count: data.citation_count
        })
        this.emit('chat:streaming_end', {
          message_id: data.message_id || 'current'
        })
        break
      }
      case 'error':
        this.emit('error', { message: data.message, code: data.code })
        break

      // Backward-compatibility: legacy workflow events
      case 'start':
        this.emit('chat:workflow_start', {
          message_id: data.message_id || 'current',
          message: data.message,
          query: data.query
        })
        break
      case 'workflow_start':
        this.emit('chat:workflow_init', {
          message_id: data.message_id || 'current',
          message: data.message
        })
        break
      case 'workflow_step':
        this.emit('chat:workflow_step', {
          message_id: data.message_id || 'current',
          step: data.step,
          message: data.message
        })
        break
      case 'workflow_result':
        console.log('Received workflow_result:', data)
        this.emit('chat:streaming_complete', {
          message_id: data.message_id || 'current',
          message: data.response,
          agent_type: data.agent_type,
          confidence: data.confidence,
          recommendations: data.recommendations || [],
          metadata: data.metadata,
          is_complete: true
        })
        break
      case 'llm_start':
        this.emit('chat:streaming_start', {
          message_id: data.message_id || 'current'
        })
        break
      case 'complete':
        this.emit('chat:streaming_end', {
          message_id: data.message_id || 'current'
        })
        break
      case 'agent_selected':
        this.emit('chat:agent_selected', {
          agent_type: data.agent_type,
          agent_name: data.agent_name,
          reasoning: data.reasoning
        })
        break
      default:
        console.log('Unknown message type:', data.type, data)
    }
  }

  private emit(event: string, data: any) {
    const listeners = this.eventListeners.get(event) || []
    listeners.forEach(listener => {
      try {
        listener(data)
      } catch (error) {
        console.error(`Error in event listener for ${event}:`, error)
      }
    })
  }

  private handleReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts && this.conversationId) {
      this.reconnectAttempts++
      setTimeout(() => {
        console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`)
        this.connect(this.conversationId!)
      }, this.reconnectDelay * this.reconnectAttempts)
    } else {
      console.error('Max reconnection attempts reached')
    }
  }

  // Chat methods
  async sendMessage(message: string, agentType?: string, messageId?: string, threadId?: string) {
    // Wait for connection to be established
    const isConnected = await this.waitForConnection()
    if (!isConnected) {
      throw new Error('WebSocket connection timeout')
    }

    const messageData = {
      type: 'chat_message',
      message,
      content: message, // Backend might expect 'content' instead of 'message'
      agent_type: agentType,
      message_id: messageId || `msg-${Date.now()}`,
      thread_id: threadId || `thread-${Date.now()}`,
      timestamp: new Date().toISOString()
    }

    console.log('Sending WebSocket message:', messageData)
    this.socket!.send(JSON.stringify(messageData))
  }

  joinConversation(conversationId: string) {
    // If already connected to this conversation, do nothing
    if (this.conversationId === conversationId && this.isConnected()) {
      console.log('Already connected to this conversation:', conversationId)
      return
    }

    // Disconnect existing connection if different conversation
    if (this.conversationId && this.conversationId !== conversationId) {
      console.log('Switching conversations, disconnecting from:', this.conversationId)
      this.disconnect()
      // Add a small delay before reconnecting
      setTimeout(() => {
        this.connect(conversationId)
      }, 200)
    } else {
      // First connection or reconnection to same conversation
      this.connect(conversationId)
    }
  }

  // Check if WebSocket is connected and ready
  isConnected(): boolean {
    return this.socket !== null && this.socket.readyState === WebSocket.OPEN
  }

  // Wait for WebSocket to be connected
  async waitForConnection(timeout: number = 5000): Promise<boolean> {
    if (this.isConnected()) {
      return true
    }

    return new Promise((resolve) => {
      const startTime = Date.now()
      const checkConnection = () => {
        if (this.isConnected()) {
          resolve(true)
        } else if (Date.now() - startTime > timeout) {
          resolve(false)
        } else {
          setTimeout(checkConnection, 100)
        }
      }
      checkConnection()
    })
  }

  // Voice methods
  startVoiceInput() {
    if (!this.socket || this.socket.readyState !== WebSocket.OPEN) {
      throw new Error('WebSocket not connected')
    }

    this.socket.send(JSON.stringify({
      type: 'voice_start',
      timestamp: new Date().toISOString()
    }))
  }

  stopVoiceInput() {
    if (!this.socket || this.socket.readyState !== WebSocket.OPEN) {
      throw new Error('WebSocket not connected')
    }

    this.socket.send(JSON.stringify({
      type: 'voice_stop',
      timestamp: new Date().toISOString()
    }))
  }

  sendVoiceData(audioBlob: Blob) {
    if (!this.socket || this.socket.readyState !== WebSocket.OPEN) {
      throw new Error('WebSocket not connected')
    }

    // Convert blob to base64 for transmission
    const reader = new FileReader()
    reader.onload = () => {
      const base64Audio = reader.result as string
      this.socket!.send(JSON.stringify({
        type: 'voice_data',
        audio: base64Audio,
        timestamp: new Date().toISOString()
      }))
    }
    reader.readAsDataURL(audioBlob)
  }

  // Event listeners
  onMessageResponse(callback: (data: {
    message: ChatMessage
    agent: string
    metadata?: any
  }) => void) {
    this.addEventListener('chat:message_response', callback)
  }

  onStreamingStart(callback: (data: { message_id: string }) => void) {
    this.addEventListener('chat:streaming_start', callback)
  }

  onStreamingChunk(callback: (data: {
    message_id: string
    chunk: string
    is_complete: boolean
  }) => void) {
    this.addEventListener('chat:streaming_chunk', callback)
  }

  onStreamingEnd(callback: (data: { message_id: string }) => void) {
    this.addEventListener('chat:streaming_end', callback)
  }

  onAgentSelected(callback: (data: {
    agent_type: string
    agent_name: string
    reasoning: string
  }) => void) {
    this.addEventListener('chat:agent_selected', callback)
  }

  onVoiceTranscript(callback: (data: { text: string; is_final: boolean }) => void) {
    this.addEventListener('voice:transcript', callback)
  }

  onVoiceResponse(callback: (data: { audio: Blob }) => void) {
    this.addEventListener('voice:response', callback)
  }

  onError(callback: (data: { message: string; code?: string }) => void) {
    this.addEventListener('error', callback)
  }

  // New workflow event handlers
  onStreamingComplete(callback: (data: {
    message_id: string
    message: string
    agent_type?: string
    confidence?: number
    recommendations?: any[]
    metadata?: any
    thread_id?: string
    is_complete: boolean
    sources?: Array<{
      title: string
      url: string
      snippet?: string
      relevance?: number
      type?: 'web' | 'database' | 'document' | 'api'
    }>
  }) => void) {
    this.addEventListener('chat:streaming_complete', callback)
  }

  onWorkflowStart(callback: (data: {
    message_id: string
    message: string
    query?: string
  }) => void) {
    this.addEventListener('chat:workflow_start', callback)
  }

  onWorkflowInit(callback: (data: {
    message_id: string
    message: string
  }) => void) {
    this.addEventListener('chat:workflow_init', callback)
  }

  onWorkflowStep(callback: (data: {
    message_id: string
    step: string
    message: string
  }) => void) {
    this.addEventListener('chat:workflow_step', callback)
  }

  // Generic event listener for any event type
  on(event: string, callback: Function) {
    this.addEventListener(event, callback)
  }

  // Utility methods

  disconnect() {
    if (this.socket) {
      // Prevent reconnection attempts
      this.reconnectAttempts = this.maxReconnectAttempts

      console.log('Disconnecting WebSocket')
      this.socket.close()
      this.socket = null
      this.conversationId = null
    }
  }

  // Event listener management
  private addEventListener(event: string, callback: Function) {
    if (!this.eventListeners.has(event)) {
      this.eventListeners.set(event, [])
    }
    this.eventListeners.get(event)!.push(callback)
  }

  off(event: string, callback?: Function) {
    if (!callback) {
      this.eventListeners.delete(event)
    } else {
      const listeners = this.eventListeners.get(event) || []
      const index = listeners.indexOf(callback)
      if (index > -1) {
        listeners.splice(index, 1)
      }
    }
  }
}

// Create singleton instance
export const webSocketService = new WebSocketService()

// React hook for WebSocket
export const useWebSocket = () => {
  return webSocketService
}
