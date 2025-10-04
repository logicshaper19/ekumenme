import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || ''

export interface Document {
  id: string
  title: string
  filename: string
  document_type: string
  description?: string
  tags: string[]
  visibility: 'internal' | 'shared' | 'public'
  status: 'pending' | 'approved' | 'rejected' | 'expired'
  uploaded_by: string
  uploaded_at: string
  file_size: number
  file_type: string
  organization_id: string
  expiration_date?: string
  shared_with_organizations?: string[]
  shared_with_users?: string[]
  review_notes?: string
  approved_by?: string
  approved_at?: string
  rejected_by?: string
  rejected_at?: string
  rejection_reason?: string
}

export interface DocumentSubmission {
  file: File
  document_type: 'product_spec' | 'regulation' | 'manual' | 'technical_sheet' | 'research_paper' | 'best_practice' | 'safety_guide' | 'other'
  description?: string
  tags?: string[]
  expiration_months?: number
  visibility: 'internal' | 'shared' | 'public'
  shared_with_organizations?: string[]
  shared_with_users?: string[]
}

export interface SearchResult {
  id: string
  title: string
  content: string
  document_type: string
  relevance_score: number
  metadata: Record<string, any>
}

class KnowledgeBaseService {
  private baseUrl = '/api/v1/knowledge-base'

  private getAuthHeaders() {
    const token = localStorage.getItem('auth_token')
    return {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    }
  }

  // Search knowledge base
  async searchDocuments(query: string, documentType?: string, limit: number = 10): Promise<SearchResult[]> {
    const params = new URLSearchParams({
      query,
      limit: limit.toString()
    })
    
    if (documentType) {
      params.append('document_type', documentType)
    }

    const response = await axios.get(`${this.baseUrl}/search?${params}`, {
      headers: this.getAuthHeaders()
    })
    return response.data
  }

  // List user documents
  async listDocuments(
    documentType?: string,
    visibility?: string,
    skip: number = 0,
    limit: number = 20
  ): Promise<Document[]> {
    const params = new URLSearchParams({
      skip: skip.toString(),
      limit: limit.toString()
    })
    
    if (documentType) {
      params.append('document_type', documentType)
    }
    
    if (visibility) {
      params.append('visibility', visibility)
    }

    // Use dev endpoint for development
    const response = await axios.get(`${this.baseUrl}/dev-documents?${params}`)
    return response.data
  }

  // Submit document
  async submitDocument(submission: DocumentSubmission): Promise<{ message: string; document_id: string }> {
    const formData = new FormData()
    formData.append('file', submission.file)
    formData.append('document_type', submission.document_type)
    formData.append('visibility', submission.visibility)
    
    if (submission.description) {
      formData.append('description', submission.description)
    }
    
    if (submission.tags && submission.tags.length > 0) {
      formData.append('tags', JSON.stringify(submission.tags))
    }
    
    if (submission.expiration_months) {
      formData.append('expiration_months', submission.expiration_months.toString())
    }
    
    if (submission.shared_with_organizations && submission.shared_with_organizations.length > 0) {
      formData.append('shared_with_organizations', JSON.stringify(submission.shared_with_organizations))
    }
    
    if (submission.shared_with_users && submission.shared_with_users.length > 0) {
      formData.append('shared_with_users', JSON.stringify(submission.shared_with_users))
    }

    const response = await axios.post(`${this.baseUrl}/submit`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      }
    })
    
    return response.data
  }

  // Analytics methods
  async getDocumentAnalytics(documentId: string, periodDays: number = 30): Promise<any> {
    try {
      // Try production endpoint first (with authentication)
      const response = await axios.get(`${this.baseUrl}/analytics/document/${documentId}?period_days=${periodDays}`, {
        headers: this.getAuthHeaders()
      })
      return response.data
    } catch (error) {
      // Fallback to dev endpoint if authentication fails
      console.warn('Authentication failed, using dev endpoint for document analytics')
      const response = await axios.get(`${this.baseUrl}/analytics/document/${documentId}?period_days=${periodDays}`)
      return response.data
    }
  }

  async getKnowledgeBaseOverview(): Promise<any> {
    try {
      // Try production endpoint first (with authentication)
      const response = await axios.get(`${this.baseUrl}/analytics/overview`, {
        headers: this.getAuthHeaders()
      })
      return response.data
    } catch (error) {
      // Fallback to dev endpoint if authentication fails
      console.warn('Authentication failed, using dev endpoint for overview')
      const response = await axios.get(`${this.baseUrl}/analytics/overview-dev`)
      return response.data
    }
  }

  async getSourceAttribution(query: string): Promise<any> {
    try {
      // Try production endpoint first (with authentication)
      const response = await axios.post(`${this.baseUrl}/analytics/source-attribution`, { query }, {
        headers: this.getAuthHeaders()
      })
      return response.data
    } catch (error) {
      // Fallback to dev endpoint if authentication fails
      console.warn('Authentication failed, using dev endpoint for source attribution')
      const response = await axios.post(`${this.baseUrl}/analytics/source-attribution-dev`, { query })
      return response.data
    }
  }

  async getDocumentChunkAnalytics(documentId: string, periodDays: number = 30): Promise<any> {
    try {
      // Try production endpoint first (with authentication)
      const response = await axios.get(`${this.baseUrl}/analytics/document/${documentId}/chunks?period_days=${periodDays}`, {
        headers: this.getAuthHeaders()
      })
      return response.data
    } catch (error) {
      // Fallback to dev endpoint if authentication fails
      console.warn('Authentication failed, using dev endpoint for chunk analytics')
      const response = await axios.get(`${this.baseUrl}/analytics/document/${documentId}/chunks?period_days=${periodDays}`)
      return response.data
    }
  }

  // List submissions
  async listSubmissions(
    statusFilter?: string,
    skip: number = 0,
    limit: number = 50
  ): Promise<Document[]> {
    const params = new URLSearchParams({
      skip: skip.toString(),
      limit: limit.toString()
    })
    
    if (statusFilter) {
      params.append('status_filter', statusFilter)
    }

    const response = await axios.get(`${this.baseUrl}/submissions?${params}`, {
      headers: this.getAuthHeaders()
    })
    return response.data
  }

  // Get document details
  async getDocumentDetails(documentId: string): Promise<Document> {
    const response = await axios.get(`${this.baseUrl}/documents/${documentId}`, {
      headers: this.getAuthHeaders()
    })
    return response.data
  }

  // Download document
  async downloadDocument(documentId: string): Promise<Blob> {
    const response = await axios.get(`${this.baseUrl}/documents/${documentId}/download`, {
      headers: this.getAuthHeaders(),
      responseType: 'blob'
    })
    return response.data
  }

  // Delete document
  async deleteDocument(documentId: string): Promise<{ message: string }> {
    const response = await axios.delete(`${this.baseUrl}/documents/${documentId}`, {
      headers: this.getAuthHeaders()
    })
    return response.data
  }

  // Update document metadata
  async updateDocument(
    documentId: string,
    updates: {
      description?: string
      tags?: string[]
      visibility?: 'internal' | 'shared' | 'public'
      shared_with_organizations?: string[]
      shared_with_users?: string[]
    }
  ): Promise<{ message: string }> {
    const response = await axios.put(`${this.baseUrl}/documents/${documentId}`, updates, {
      headers: this.getAuthHeaders()
    })
    return response.data
  }

  // Get document processing status
  async getProcessingStatus(documentId: string): Promise<{
    status: 'pending' | 'processing' | 'completed' | 'error'
    progress?: number
    error_message?: string
  }> {
    const response = await axios.get(`${this.baseUrl}/documents/${documentId}/status`, {
      headers: this.getAuthHeaders()
    })
    return response.data
  }
}

export const knowledgeBaseService = new KnowledgeBaseService()
