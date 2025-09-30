/**
 * Feedback Service
 * Handles API calls for user feedback on AI responses
 */

import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export interface FeedbackSubmission {
  message_id: string
  conversation_id: string
  feedback_type: 'thumbs_up' | 'thumbs_down'
  feedback_category?: 'incorrect' | 'incomplete' | 'irrelevant' | 'unclear' | 'slow' | 'other'
  comment?: string
  query_text?: string
  response_text?: string
  context_metadata?: Record<string, any>
}

export interface FeedbackResponse {
  id: string
  message_id: string
  conversation_id: string
  feedback_type: 'thumbs_up' | 'thumbs_down'
  feedback_category?: string
  comment?: string
  reviewed: boolean
  created_at: string
}

export interface FeedbackStats {
  total_feedback: number
  thumbs_up: number
  thumbs_down: number
  thumbs_up_rate: number
  needs_review: number
  reviewed: number
}

class FeedbackService {
  private getAuthHeaders() {
    const token = localStorage.getItem('access_token')
    return {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    }
  }

  /**
   * Submit feedback on an AI response
   */
  async submitFeedback(feedback: FeedbackSubmission): Promise<FeedbackResponse> {
    try {
      const response = await axios.post(
        `${API_BASE_URL}/api/v1/feedback/`,
        feedback,
        { headers: this.getAuthHeaders() }
      )
      return response.data
    } catch (error) {
      console.error('Error submitting feedback:', error)
      throw error
    }
  }

  /**
   * Get feedback for a specific message
   */
  async getMessageFeedback(messageId: string): Promise<FeedbackResponse | null> {
    try {
      const response = await axios.get(
        `${API_BASE_URL}/api/v1/feedback/message/${messageId}`,
        { headers: this.getAuthHeaders() }
      )
      return response.data
    } catch (error) {
      console.error('Error getting message feedback:', error)
      return null
    }
  }

  /**
   * Get all feedback for a conversation
   */
  async getConversationFeedback(conversationId: string): Promise<FeedbackResponse[]> {
    try {
      const response = await axios.get(
        `${API_BASE_URL}/api/v1/feedback/conversation/${conversationId}`,
        { headers: this.getAuthHeaders() }
      )
      return response.data
    } catch (error) {
      console.error('Error getting conversation feedback:', error)
      return []
    }
  }

  /**
   * Get feedback statistics for the current user
   */
  async getFeedbackStats(): Promise<FeedbackStats> {
    try {
      const response = await axios.get(
        `${API_BASE_URL}/api/v1/feedback/stats`,
        { headers: this.getAuthHeaders() }
      )
      return response.data
    } catch (error) {
      console.error('Error getting feedback stats:', error)
      throw error
    }
  }

  /**
   * Delete feedback
   */
  async deleteFeedback(feedbackId: string): Promise<void> {
    try {
      await axios.delete(
        `${API_BASE_URL}/api/v1/feedback/${feedbackId}`,
        { headers: this.getAuthHeaders() }
      )
    } catch (error) {
      console.error('Error deleting feedback:', error)
      throw error
    }
  }
}

export const feedbackService = new FeedbackService()

