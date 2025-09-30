import React, { useState } from 'react'
import { ThumbsUp, ThumbsDown, Copy, Check } from 'lucide-react'
import { feedbackService } from '../services/feedbackService'

interface MessageActionsProps {
  messageId: string
  conversationId: string
  content: string
  queryText?: string
  onFeedbackSubmitted?: () => void
}

interface FeedbackModalProps {
  isOpen: boolean
  onClose: () => void
  onSubmit: (category: string, comment: string) => void
}

const FeedbackModal: React.FC<FeedbackModalProps> = ({ isOpen, onClose, onSubmit }) => {
  const [category, setCategory] = useState('')
  const [comment, setComment] = useState('')

  if (!isOpen) return null

  const handleSubmit = () => {
    onSubmit(category, comment)
    setCategory('')
    setComment('')
  }

  const categories = [
    { value: 'incorrect', label: 'Informations incorrectes' },
    { value: 'incomplete', label: 'Réponse incomplète' },
    { value: 'irrelevant', label: 'Hors sujet' },
    { value: 'unclear', label: 'Pas clair' },
    { value: 'slow', label: 'Trop lent' },
    { value: 'other', label: 'Autre' }
  ]

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          Aidez-nous à améliorer
        </h3>
        
        <div className="space-y-4">
          {/* Category Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Quel est le problème ? (optionnel)
            </label>
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
            >
              <option value="">Sélectionnez une catégorie</option>
              {categories.map((cat) => (
                <option key={cat.value} value={cat.value}>
                  {cat.label}
                </option>
              ))}
            </select>
          </div>

          {/* Comment */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Commentaire (optionnel)
            </label>
            <textarea
              value={comment}
              onChange={(e) => setComment(e.target.value)}
              placeholder="Dites-nous ce qui n'a pas fonctionné..."
              className="w-full px-3 py-2 border border-gray-300 rounded-lg resize-none focus:ring-2 focus:ring-green-500 focus:border-transparent"
              rows={4}
            />
          </div>

          {/* Buttons */}
          <div className="flex gap-3 justify-end">
            <button
              onClick={onClose}
              className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
            >
              Annuler
            </button>
            <button
              onClick={handleSubmit}
              className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
            >
              Envoyer
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

const MessageActions: React.FC<MessageActionsProps> = ({
  messageId,
  conversationId,
  content,
  queryText,
  onFeedbackSubmitted
}) => {
  const [feedback, setFeedback] = useState<'thumbs_up' | 'thumbs_down' | null>(null)
  const [copied, setCopied] = useState(false)
  const [showFeedbackModal, setShowFeedbackModal] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(content)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch (error) {
      console.error('Failed to copy:', error)
    }
  }

  const handleThumbsUp = async () => {
    if (feedback === 'thumbs_up') {
      // Already thumbs up, do nothing or allow toggle
      return
    }

    setIsSubmitting(true)
    try {
      await feedbackService.submitFeedback({
        message_id: messageId,
        conversation_id: conversationId,
        feedback_type: 'thumbs_up',
        query_text: queryText,
        response_text: content
      })
      
      setFeedback('thumbs_up')
      onFeedbackSubmitted?.()
    } catch (error) {
      console.error('Failed to submit feedback:', error)
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleThumbsDown = () => {
    if (feedback === 'thumbs_down') {
      // Already thumbs down, do nothing or allow toggle
      return
    }

    // Show modal for detailed feedback
    setShowFeedbackModal(true)
  }

  const handleFeedbackModalSubmit = async (category: string, comment: string) => {
    setIsSubmitting(true)
    try {
      await feedbackService.submitFeedback({
        message_id: messageId,
        conversation_id: conversationId,
        feedback_type: 'thumbs_down',
        feedback_category: category || undefined,
        comment: comment || undefined,
        query_text: queryText,
        response_text: content
      })
      
      setFeedback('thumbs_down')
      setShowFeedbackModal(false)
      onFeedbackSubmitted?.()
    } catch (error) {
      console.error('Failed to submit feedback:', error)
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <>
      <div className="flex items-center gap-2 mt-2">
        {/* Thumbs Up */}
        <button
          onClick={handleThumbsUp}
          disabled={isSubmitting}
          className={`p-1.5 rounded-lg transition-all ${
            feedback === 'thumbs_up'
              ? 'bg-green-100 text-green-600'
              : 'text-gray-400 hover:text-green-600 hover:bg-green-50'
          } disabled:opacity-50 disabled:cursor-not-allowed`}
          title="Bonne réponse"
        >
          <ThumbsUp className="h-4 w-4" />
        </button>

        {/* Thumbs Down */}
        <button
          onClick={handleThumbsDown}
          disabled={isSubmitting}
          className={`p-1.5 rounded-lg transition-all ${
            feedback === 'thumbs_down'
              ? 'bg-red-100 text-red-600'
              : 'text-gray-400 hover:text-red-600 hover:bg-red-50'
          } disabled:opacity-50 disabled:cursor-not-allowed`}
          title="Mauvaise réponse"
        >
          <ThumbsDown className="h-4 w-4" />
        </button>

        {/* Copy Button */}
        <button
          onClick={handleCopy}
          className={`p-1.5 rounded-lg transition-all ${
            copied
              ? 'bg-blue-100 text-blue-600'
              : 'text-gray-400 hover:text-blue-600 hover:bg-blue-50'
          }`}
          title={copied ? 'Copié !' : 'Copier la réponse'}
        >
          {copied ? (
            <Check className="h-4 w-4" />
          ) : (
            <Copy className="h-4 w-4" />
          )}
        </button>
      </div>

      {/* Feedback Modal */}
      <FeedbackModal
        isOpen={showFeedbackModal}
        onClose={() => setShowFeedbackModal(false)}
        onSubmit={handleFeedbackModalSubmit}
      />
    </>
  )
}

export default MessageActions

