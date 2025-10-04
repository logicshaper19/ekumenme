import { webSocketService } from './websocket'

export interface FarmDataUpdate {
  type: 'parcelle' | 'intervention' | 'exploitation' | 'dashboard'
  action: 'created' | 'updated' | 'deleted'
  data: any
  timestamp: string
  farm_siret?: string
  parcelle_id?: string
  intervention_id?: string
}

export interface FarmDataSubscription {
  farm_siret?: string
  parcelle_id?: string
  intervention_id?: string
  types?: ('parcelle' | 'intervention' | 'exploitation' | 'dashboard')[]
}

class FarmRealtimeService {
  private subscriptions: Map<string, FarmDataSubscription> = new Map()
  private updateCallbacks: Map<string, Function[]> = new Map()
  private isConnected = false

  constructor() {
    this.setupWebSocketListeners()
  }

  private setupWebSocketListeners() {
    // Listen for farm WebSocket connection events
    webSocketService.on('farm:connect', () => {
      this.isConnected = true
      this.resubscribeAll()
    })

    webSocketService.on('farm:disconnect', () => {
      this.isConnected = false
    })

    // Listen for farm data updates
    webSocketService.on('farm:data_update', (data: FarmDataUpdate) => {
      this.handleFarmDataUpdate(data)
    })

    // Listen for specific farm data events
    webSocketService.on('farm:parcelle_update', (data: any) => {
      this.handleFarmDataUpdate({
        type: 'parcelle',
        action: 'updated',
        data,
        timestamp: new Date().toISOString()
      })
    })

    webSocketService.on('farm:intervention_update', (data: any) => {
      this.handleFarmDataUpdate({
        type: 'intervention',
        action: 'updated',
        data,
        timestamp: new Date().toISOString()
      })
    })

    webSocketService.on('farm:exploitation_update', (data: any) => {
      this.handleFarmDataUpdate({
        type: 'exploitation',
        action: 'updated',
        data,
        timestamp: new Date().toISOString()
      })
    })
  }

  private handleFarmDataUpdate(update: FarmDataUpdate) {
    // Notify all relevant subscribers
    this.updateCallbacks.forEach((callbacks, key) => {
      const subscription = this.subscriptions.get(key)
      if (subscription && this.isUpdateRelevant(update, subscription)) {
        callbacks.forEach(callback => {
          try {
            callback(update)
          } catch (error) {
            console.error('Error in farm data update callback:', error)
          }
        })
      }
    })
  }

  private isUpdateRelevant(update: FarmDataUpdate, subscription: FarmDataSubscription): boolean {
    // Check if update type matches subscription
    if (subscription.types && !subscription.types.includes(update.type)) {
      return false
    }

    // Check farm SIRET match
    if (subscription.farm_siret && update.farm_siret && subscription.farm_siret !== update.farm_siret) {
      return false
    }

    // Check parcelle ID match
    if (subscription.parcelle_id && update.parcelle_id && subscription.parcelle_id !== update.parcelle_id) {
      return false
    }

    // Check intervention ID match
    if (subscription.intervention_id && update.intervention_id && subscription.intervention_id !== update.intervention_id) {
      return false
    }

    return true
  }

  private resubscribeAll() {
    if (!this.isConnected) return

    this.subscriptions.forEach((subscription, key) => {
      this.sendSubscription(subscription)
    })
  }

  private sendSubscription(subscription: FarmDataSubscription) {
    if (!this.isConnected) return

    // Send via WebSocket
    if (webSocketService.isFarmConnected()) {
      webSocketService.subscribeToFarmUpdates(subscription)
    }
  }

  // Public methods

  /**
   * Subscribe to farm data updates
   * @param subscription - What data to subscribe to
   * @param callback - Callback function for updates
   * @returns Subscription ID for unsubscribing
   */
  subscribe(
    subscription: FarmDataSubscription,
    callback: (update: FarmDataUpdate) => void
  ): string {
    const subscriptionId = `farm_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
    
    this.subscriptions.set(subscriptionId, subscription)
    
    if (!this.updateCallbacks.has(subscriptionId)) {
      this.updateCallbacks.set(subscriptionId, [])
    }
    this.updateCallbacks.get(subscriptionId)!.push(callback)

    // Send subscription to server
    this.sendSubscription(subscription)

    return subscriptionId
  }

  /**
   * Unsubscribe from farm data updates
   * @param subscriptionId - ID returned from subscribe()
   */
  unsubscribe(subscriptionId: string) {
    this.subscriptions.delete(subscriptionId)
    this.updateCallbacks.delete(subscriptionId)

    // Send unsubscribe message to server
    if (this.isConnected && webSocketService.isFarmConnected()) {
      webSocketService.unsubscribeFromFarmUpdates(subscriptionId)
    }
  }

  /**
   * Subscribe to all updates for a specific farm
   */
  subscribeToFarm(
    farm_siret: string,
    callback: (update: FarmDataUpdate) => void
  ): string {
    return this.subscribe(
      { farm_siret, types: ['parcelle', 'intervention', 'exploitation', 'dashboard'] },
      callback
    )
  }

  /**
   * Subscribe to updates for a specific parcelle
   */
  subscribeToParcelle(
    parcelle_id: string,
    callback: (update: FarmDataUpdate) => void
  ): string {
    return this.subscribe(
      { parcelle_id, types: ['parcelle', 'intervention'] },
      callback
    )
  }

  /**
   * Subscribe to updates for a specific intervention
   */
  subscribeToIntervention(
    intervention_id: string,
    callback: (update: FarmDataUpdate) => void
  ): string {
    return this.subscribe(
      { intervention_id, types: ['intervention'] },
      callback
    )
  }

  /**
   * Subscribe to dashboard updates for a farm
   */
  subscribeToDashboard(
    farm_siret: string,
    callback: (update: FarmDataUpdate) => void
  ): string {
    return this.subscribe(
      { farm_siret, types: ['dashboard'] },
      callback
    )
  }

  /**
   * Check if the service is connected
   */
  isServiceConnected(): boolean {
    return this.isConnected && webSocketService.isFarmConnected()
  }

  /**
   * Connect to farm WebSocket
   */
  connect() {
    webSocketService.connectToFarmUpdates()
  }

  /**
   * Disconnect from farm WebSocket
   */
  disconnect() {
    webSocketService.disconnectFromFarmUpdates()
  }

  /**
   * Get current subscription count
   */
  getSubscriptionCount(): number {
    return this.subscriptions.size
  }
}

// Create singleton instance
export const farmRealtimeService = new FarmRealtimeService()

// React hook for farm real-time updates
export const useFarmRealtime = () => {
  return farmRealtimeService
}

// Helper hook for subscribing to farm updates
export const useFarmUpdates = (
  subscription: FarmDataSubscription,
  callback: (update: FarmDataUpdate) => void,
  deps: any[] = []
) => {
  const { subscribe, unsubscribe } = farmRealtimeService

  React.useEffect(() => {
    const subscriptionId = subscribe(subscription, callback)
    return () => unsubscribe(subscriptionId)
  }, deps)
}

// Helper hook for subscribing to farm updates with automatic data refresh
export const useFarmDataWithUpdates = <T>(
  fetchFunction: () => Promise<T>,
  subscription: FarmDataSubscription,
  deps: any[] = []
): { data: T | null; loading: boolean; error: string | null; refetch: () => void } => {
  const [data, setData] = React.useState<T | null>(null)
  const [loading, setLoading] = React.useState(true)
  const [error, setError] = React.useState<string | null>(null)

  const fetchData = React.useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      const result = await fetchFunction()
      setData(result)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch data')
    } finally {
      setLoading(false)
    }
  }, deps)

  // Initial fetch
  React.useEffect(() => {
    fetchData()
  }, [fetchData])

  // Subscribe to real-time updates
  useFarmUpdates(subscription, () => {
    // Refetch data when updates are received
    fetchData()
  }, deps)

  return {
    data,
    loading,
    error,
    refetch: fetchData
  }
}

// Import React for hooks
import React from 'react'
