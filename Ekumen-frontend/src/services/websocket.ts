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
      const token = localStorage.getItem('auth_token')
      const wsUrl = process.env.REACT_APP_WS_URL || 'ws://localhost:8000'
      const url = `${wsUrl}/api/v1/chat/ws/${conversationId}?token=${token}`

      this.socket = new WebSocket(url)
      this.conversationId = conversationId
      this.setupEventListeners()
    } catch (error) {
      console.error('Failed to connect to WebSocket:', error)
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
      case 'token':
        this.emit('chat:streaming_chunk', {
          message_id: data.message_id || 'current',
          chunk: data.token,
          is_complete: false
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
      case 'error':
        this.emit('error', {
          message: data.message,
          code: data.code
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
  sendMessage(message: string, agentType?: string) {
    if (!this.socket || this.socket.readyState !== WebSocket.OPEN) {
      throw new Error('WebSocket not connected')
    }

    const messageData = {
      type: 'chat_message',
      message,
      agent_type: agentType,
      timestamp: new Date().toISOString()
    }

    this.socket.send(JSON.stringify(messageData))
  }

  joinConversation(conversationId: string) {
    if (!this.conversationId) {
      this.connect(conversationId)
    } else if (this.conversationId !== conversationId) {
      this.disconnect()
      this.connect(conversationId)
    }
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

  // Utility methods
  isConnected(): boolean {
    return this.socket?.readyState === WebSocket.OPEN
  }

  disconnect() {
    if (this.socket) {
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
