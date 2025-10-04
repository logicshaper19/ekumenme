import React, { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { 
  FileText, 
  Upload, 
  Search, 
  Filter, 
  Download, 
  Eye, 
  Edit, 
  Trash2, 
  Plus,
  File,
  Image,
  FileType,
  CheckCircle,
  AlertCircle,
  Clock,
  Tag,
  Calendar,
  Loader2,
  BarChart3,
  TrendingUp,
  Users,
  MessageSquare,
  X,
  Activity,
  Target,
  Zap
} from 'lucide-react'
import { knowledgeBaseService, Document, DocumentSubmission } from '@services/knowledgeBaseService'

const DocumentsTab: React.FC = () => {
  const [documents, setDocuments] = useState<Document[]>([])
  const [filteredDocuments, setFilteredDocuments] = useState<Document[]>([])
  const [searchTerm, setSearchTerm] = useState('')
  const [filterStatus, setFilterStatus] = useState<string>('all')
  const [filterType, setFilterType] = useState<string>('all')
  const [showUploadModal, setShowUploadModal] = useState(false)
  const [selectedFiles, setSelectedFiles] = useState<FileList | null>(null)
  const [loading, setLoading] = useState(true)
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [uploadForm, setUploadForm] = useState({
    document_type: 'other' as const,
    description: '',
    visibility: 'internal' as const,
    tags: [] as string[],
    expiration_months: 12
  })
  
  // Document detail modal state
  const [showDocumentModal, setShowDocumentModal] = useState(false)
  const [selectedDocument, setSelectedDocument] = useState<Document | null>(null)
  const [documentAnalytics, setDocumentAnalytics] = useState<any>(null)
  const [analyticsLoading, setAnalyticsLoading] = useState(false)
  const [sourceAttributionQuery, setSourceAttributionQuery] = useState('')
  const [sourceAttribution, setSourceAttribution] = useState<any>(null)
  const [attributionLoading, setAttributionLoading] = useState(false)
  const [chunkAnalytics, setChunkAnalytics] = useState<any>(null)
  const [chunkAnalyticsLoading, setChunkAnalyticsLoading] = useState(false)

  // Load documents from API
  useEffect(() => {
    const loadDocuments = async () => {
      try {
        setLoading(true)
        setError(null)
        const docs = await knowledgeBaseService.listDocuments()
        setDocuments(docs)
        setFilteredDocuments(docs)
      } catch (err) {
        console.error('Error loading documents:', err)
        setError('Erreur lors du chargement des documents')
      } finally {
        setLoading(false)
      }
    }

    loadDocuments()
  }, [])

  // Filter documents
  useEffect(() => {
    let filtered = documents

    if (searchTerm) {
      filtered = filtered.filter(doc => 
        doc.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
        doc.description?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        doc.tags.some(tag => tag.toLowerCase().includes(searchTerm.toLowerCase()))
      )
    }

    if (filterStatus !== 'all') {
      filtered = filtered.filter(doc => doc.status === filterStatus)
    }

    if (filterType !== 'all') {
      filtered = filtered.filter(doc => doc.document_type === filterType)
    }

    setFilteredDocuments(filtered)
  }, [documents, searchTerm, filterStatus, filterType])

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'approved':
        return <CheckCircle className="h-4 w-4 text-green-500" />
      case 'pending':
        return <Clock className="h-4 w-4 text-yellow-500" />
      case 'rejected':
        return <AlertCircle className="h-4 w-4 text-red-500" />
      case 'expired':
        return <AlertCircle className="h-4 w-4 text-orange-500" />
      default:
        return <Clock className="h-4 w-4 text-gray-400" />
    }
  }

  const getStatusText = (status: string) => {
    switch (status) {
      case 'approved':
        return 'Approuvé'
      case 'pending':
        return 'En attente'
      case 'rejected':
        return 'Rejeté'
      case 'expired':
        return 'Expiré'
      default:
        return 'Inconnu'
    }
  }

  const getTypeIcon = (fileType: string | undefined) => {
    if (!fileType) return <File className="h-4 w-4 text-gray-500" />
    
    const type = fileType.toLowerCase()
    if (type.includes('pdf')) {
      return <FileType className="h-4 w-4 text-red-500" />
    } else if (type.includes('image') || type.includes('jpg') || type.includes('png') || type.includes('jpeg')) {
      return <Image className="h-4 w-4 text-blue-500" />
    } else if (type.includes('text') || type.includes('txt') || type.includes('md')) {
      return <FileText className="h-4 w-4 text-green-500" />
    } else {
      return <File className="h-4 w-4 text-gray-500" />
    }
  }

  const formatFileSize = (sizeInBytes: number) => {
    if (sizeInBytes < 1024) {
      return `${sizeInBytes} B`
    } else if (sizeInBytes < 1024 * 1024) {
      return `${(sizeInBytes / 1024).toFixed(0)} KB`
    } else {
      return `${(sizeInBytes / (1024 * 1024)).toFixed(1)} MB`
    }
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleDateString('fr-FR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric'
    })
  }

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    setSelectedFiles(event.target.files)
  }

  const handleUpload = async () => {
    if (!selectedFiles || selectedFiles.length === 0) return

    try {
      setUploading(true)
      setError(null)

      // Upload each file
      for (let i = 0; i < selectedFiles.length; i++) {
        const file = selectedFiles[i]
        const submission: DocumentSubmission = {
          file,
          document_type: uploadForm.document_type,
          description: uploadForm.description || `Document uploadé: ${file.name}`,
          visibility: uploadForm.visibility,
          tags: uploadForm.tags,
          expiration_months: uploadForm.expiration_months
        }

        await knowledgeBaseService.submitDocument(submission)
      }

      // Reload documents
      const docs = await knowledgeBaseService.listDocuments()
      setDocuments(docs)
      setFilteredDocuments(docs)

      // Reset form and close modal
      setShowUploadModal(false)
      setSelectedFiles(null)
      setUploadForm({
        document_type: 'other',
        description: '',
        visibility: 'internal',
        tags: [],
        expiration_months: 12
      })
    } catch (err) {
      console.error('Error uploading files:', err)
      setError('Erreur lors du téléchargement des fichiers')
    } finally {
      setUploading(false)
    }
  }

  // Handle document detail view
  const handleViewDocument = async (document: Document) => {
    setSelectedDocument(document)
    setShowDocumentModal(true)
    setAnalyticsLoading(true)
    setDocumentAnalytics(null)
    setSourceAttribution(null)
    setSourceAttributionQuery('')

    try {
      // Load document analytics
      const analytics = await knowledgeBaseService.getDocumentAnalytics(document.id)
      setDocumentAnalytics(analytics)
    } catch (err) {
      console.error('Error loading document analytics:', err)
    } finally {
      setAnalyticsLoading(false)
    }
  }

  // Handle source attribution query
  const handleSourceAttribution = async () => {
    if (!sourceAttributionQuery.trim() || !selectedDocument) return

    setAttributionLoading(true)
    try {
      const attribution = await knowledgeBaseService.getSourceAttribution(sourceAttributionQuery)
      setSourceAttribution(attribution)
    } catch (err) {
      console.error('Error getting source attribution:', err)
    } finally {
      setAttributionLoading(false)
    }
  }

  const loadChunkAnalytics = async () => {
    if (!selectedDocument) return
    
    setChunkAnalyticsLoading(true)
    try {
      const result = await knowledgeBaseService.getDocumentChunkAnalytics(selectedDocument.id, 30)
      setChunkAnalytics(result)
    } catch (error) {
      console.error('Error getting chunk analytics:', error)
      setError('Erreur lors du chargement des analytics de chunks')
    } finally {
      setChunkAnalyticsLoading(false)
    }
  }

  // Close document modal
  const closeDocumentModal = () => {
    setShowDocumentModal(false)
    setSelectedDocument(null)
    setDocumentAnalytics(null)
    setSourceAttribution(null)
    setSourceAttributionQuery('')
  }

  return (
    <div className="space-y-6">
      {/* Header with Upload Button */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold text-gray-900">Mes Documents</h2>
          <p className="text-sm text-gray-600 mt-1">
            Gérez votre base documentaire et suivez le traitement de vos fichiers
          </p>
        </div>
        <button
          onClick={() => setShowUploadModal(true)}
          className="btn-primary flex items-center gap-2"
        >
          <Upload className="h-4 w-4" />
          Ajouter des documents
        </button>
      </div>

      {/* Statistics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="card p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Total Documents</p>
              <p className="text-2xl font-bold text-gray-900">{documents.length}</p>
            </div>
            <FileText className="h-8 w-8 text-blue-500" />
          </div>
        </div>
        
        <div className="card p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Approuvés</p>
              <p className="text-2xl font-bold text-green-600">
                {documents.filter(d => d.status === 'approved').length}
              </p>
            </div>
            <CheckCircle className="h-8 w-8 text-green-500" />
          </div>
        </div>
        
        <div className="card p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">En attente</p>
              <p className="text-2xl font-bold text-yellow-600">
                {documents.filter(d => d.status === 'pending').length}
              </p>
            </div>
            <Clock className="h-8 w-8 text-yellow-500" />
          </div>
        </div>
        
        <div className="card p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Rejetés</p>
              <p className="text-2xl font-bold text-red-600">
                {documents.filter(d => d.status === 'rejected').length}
              </p>
            </div>
            <AlertCircle className="h-8 w-8 text-red-500" />
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="card p-4">
        <div className="flex flex-col md:flex-row gap-4">
          {/* Search */}
          <div className="flex-1">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
              <input
                type="text"
                placeholder="Rechercher dans les documents..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="input pl-10"
              />
            </div>
          </div>

          {/* Status Filter */}
          <div>
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="input"
            >
              <option value="all">Tous les statuts</option>
              <option value="approved">Approuvé</option>
              <option value="pending">En attente</option>
              <option value="rejected">Rejeté</option>
              <option value="expired">Expiré</option>
            </select>
          </div>

          {/* Type Filter */}
          <div>
            <select
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
              className="input"
            >
              <option value="all">Tous les types</option>
              <option value="technical_document">Document technique</option>
              <option value="regulatory_document">Document réglementaire</option>
              <option value="research_paper">Article de recherche</option>
              <option value="manual">Manuel</option>
              <option value="other">Autre</option>
            </select>
          </div>
        </div>
      </div>

      {/* Documents List */}
      <div className="card">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">Documents ({filteredDocuments.length})</h3>
        </div>
        
        <div className="divide-y divide-gray-200">
          {loading ? (
            <div className="p-8 text-center text-gray-500">
              <Loader2 className="h-12 w-12 mx-auto mb-4 text-gray-300 animate-spin" />
              <p>Chargement des documents...</p>
            </div>
          ) : error ? (
            <div className="p-8 text-center text-red-500">
              <AlertCircle className="h-12 w-12 mx-auto mb-4 text-red-300" />
              <p>{error}</p>
              <button
                onClick={() => window.location.reload()}
                className="mt-2 text-sm text-blue-600 hover:text-blue-800"
              >
                Réessayer
              </button>
            </div>
          ) : filteredDocuments.length === 0 ? (
            <div className="p-8 text-center text-gray-500">
              <FileText className="h-12 w-12 mx-auto mb-4 text-gray-300" />
              <p>Aucun document trouvé</p>
              <p className="text-sm">Modifiez vos filtres ou ajoutez de nouveaux documents</p>
            </div>
          ) : (
            filteredDocuments.map((doc) => (
              <motion.div
                key={doc.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="p-6 hover:bg-gray-50 transition-colors"
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-start space-x-4 flex-1">
                    {/* File Icon */}
                    <div className="flex-shrink-0">
                      {getTypeIcon(doc.file_type)}
                    </div>
                    
                    {/* Document Info */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center space-x-2 mb-1">
                        <h4 className="text-sm font-medium text-gray-900 truncate">
                          {doc.title}
                        </h4>
                        <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                          {doc.document_type}
                        </span>
                      </div>
                      
                      {doc.description && (
                        <p className="text-sm text-gray-600 mb-2">{doc.description}</p>
                      )}
                      
                      <div className="flex items-center space-x-4 text-xs text-gray-500">
                        <span className="flex items-center">
                          <Calendar className="h-3 w-3 mr-1" />
                          {formatDate(doc.uploaded_at)}
                        </span>
                        <span>{doc.file_size ? formatFileSize(doc.file_size) : 'N/A'}</span>
                        <span className="flex items-center">
                          <Tag className="h-3 w-3 mr-1" />
                          {doc.visibility}
                        </span>
                      </div>
                      
                      {/* Tags */}
                      <div className="flex items-center space-x-1 mt-2">
                        {doc.tags.map((tag) => (
                          <span
                            key={tag}
                            className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-gray-100 text-gray-800"
                          >
                            <Tag className="h-3 w-3 mr-1" />
                            {tag}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>
                  
                  {/* Status and Actions */}
                  <div className="flex items-center space-x-3">
                    <div className="flex items-center space-x-1">
                      {getStatusIcon(doc.status)}
                      <span className="text-sm text-gray-600">
                        {getStatusText(doc.status)}
                      </span>
                    </div>
                    
                    <div className="flex items-center space-x-1">
                      <button
                        onClick={() => handleViewDocument(doc)}
                        className="p-1 text-gray-400 hover:text-gray-600"
                        title="Voir les détails et analytics"
                      >
                        <Eye className="h-4 w-4" />
                      </button>
                      <button
                        className="p-1 text-gray-400 hover:text-gray-600"
                        title="Télécharger"
                      >
                        <Download className="h-4 w-4" />
                      </button>
                      <button
                        className="p-1 text-gray-400 hover:text-gray-600"
                        title="Modifier"
                      >
                        <Edit className="h-4 w-4" />
                      </button>
                      <button
                        className="p-1 text-gray-400 hover:text-red-600"
                        title="Supprimer"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                </div>
              </motion.div>
            ))
          )}
        </div>
      </div>

      {/* Upload Modal */}
      {showUploadModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white p-6 rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <h3 className="text-xl font-semibold text-gray-900 mb-6">Ajouter des documents</h3>
            
            <div className="space-y-6">
              {/* File Selection */}
              <div>
                <label htmlFor="file-upload" className="block text-sm font-medium text-gray-700 mb-2">
                  Sélectionner des fichiers
                </label>
                <input
                  id="file-upload"
                  type="file"
                  multiple
                  accept=".pdf,.jpg,.jpeg,.png,.txt,.doc,.docx"
                  onChange={handleFileUpload}
                  className="block w-full text-sm text-gray-500
                    file:mr-4 file:py-2 file:px-4
                    file:rounded-md file:border-0
                    file:text-sm file:font-semibold
                    file:bg-blue-50 file:text-blue-700
                    hover:file:bg-blue-100"
                />
                {selectedFiles && (
                  <div className="mt-2">
                    <p className="text-sm text-gray-500 mb-2">
                      {selectedFiles.length} fichier(s) sélectionné(s):
                    </p>
                    <div className="space-y-1">
                      {Array.from(selectedFiles).map((file, index) => (
                        <div key={index} className="text-xs text-gray-600 bg-gray-50 p-2 rounded">
                          {file.name} ({(file.size / 1024 / 1024).toFixed(2)} MB)
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* Document Type */}
              <div>
                <label htmlFor="document-type" className="block text-sm font-medium text-gray-700 mb-2">
                  Type de document
                </label>
                <select
                  id="document-type"
                  value={uploadForm.document_type}
                  onChange={(e) => setUploadForm(prev => ({ ...prev, document_type: e.target.value as any }))}
                  className="input"
                >
                  <option value="product_spec">Spécification de produit</option>
                  <option value="regulation">Réglementation</option>
                  <option value="manual">Manuel</option>
                  <option value="technical_sheet">Fiche technique</option>
                  <option value="research_paper">Article de recherche</option>
                  <option value="best_practice">Bonnes pratiques</option>
                  <option value="safety_guide">Guide de sécurité</option>
                  <option value="other">Autre</option>
                </select>
              </div>

              {/* Description */}
              <div>
                <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-2">
                  Description (optionnel)
                </label>
                <textarea
                  id="description"
                  value={uploadForm.description}
                  onChange={(e) => setUploadForm(prev => ({ ...prev, description: e.target.value }))}
                  rows={3}
                  className="input"
                  placeholder="Décrivez le contenu de ce document..."
                />
              </div>

              {/* Visibility */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Visibilité
                </label>
                <div className="space-y-2">
                  <label className="flex items-center">
                    <input
                      type="radio"
                      name="visibility"
                      value="internal"
                      checked={uploadForm.visibility === 'internal'}
                      onChange={(e) => setUploadForm(prev => ({ ...prev, visibility: e.target.value as any }))}
                      className="mr-2"
                    />
                    <span className="text-sm text-gray-700">
                      <strong>Interne</strong> - Visible uniquement par votre organisation
                    </span>
                  </label>
                  <label className="flex items-center">
                    <input
                      type="radio"
                      name="visibility"
                      value="shared"
                      checked={uploadForm.visibility === 'shared'}
                      onChange={(e) => setUploadForm(prev => ({ ...prev, visibility: e.target.value as any }))}
                      className="mr-2"
                    />
                    <span className="text-sm text-gray-700">
                      <strong>Partagé</strong> - Visible par des organisations spécifiques
                    </span>
                  </label>
                  <label className="flex items-center">
                    <input
                      type="radio"
                      name="visibility"
                      value="public"
                      checked={uploadForm.visibility === 'public'}
                      onChange={(e) => setUploadForm(prev => ({ ...prev, visibility: e.target.value as any }))}
                      className="mr-2"
                    />
                    <span className="text-sm text-gray-700">
                      <strong>Public</strong> - Visible par tous les utilisateurs
                    </span>
                  </label>
                </div>
              </div>

              {/* Expiration */}
              <div>
                <label htmlFor="expiration" className="block text-sm font-medium text-gray-700 mb-2">
                  Durée de validité (mois)
                </label>
                <select
                  id="expiration"
                  value={uploadForm.expiration_months}
                  onChange={(e) => setUploadForm(prev => ({ ...prev, expiration_months: parseInt(e.target.value) }))}
                  className="input"
                >
                  <option value={6}>6 mois</option>
                  <option value={12}>12 mois</option>
                  <option value={24}>24 mois</option>
                  <option value={36}>36 mois</option>
                  <option value={0}>Pas d'expiration</option>
                </select>
              </div>

              {/* Tags */}
              <div>
                <label htmlFor="tags" className="block text-sm font-medium text-gray-700 mb-2">
                  Tags (optionnel)
                </label>
                <input
                  id="tags"
                  type="text"
                  value={uploadForm.tags.join(', ')}
                  onChange={(e) => setUploadForm(prev => ({ 
                    ...prev, 
                    tags: e.target.value.split(',').map(tag => tag.trim()).filter(tag => tag.length > 0)
                  }))}
                  className="input"
                  placeholder="agriculture, pesticides, sécurité, ..."
                />
                <p className="text-xs text-gray-500 mt-1">Séparez les tags par des virgules</p>
              </div>
            </div>

            {error && (
              <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-md">
                <p className="text-red-600 text-sm">{error}</p>
              </div>
            )}

            <div className="flex justify-end space-x-4 mt-6">
              <button
                onClick={() => {
                  setShowUploadModal(false)
                  setSelectedFiles(null)
                  setUploadForm({
                    document_type: 'other',
                    description: '',
                    visibility: 'internal',
                    tags: [],
                    expiration_months: 12
                  })
                }}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200"
              >
                Annuler
              </button>
              <button
                onClick={handleUpload}
                disabled={!selectedFiles || uploading}
                className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
              >
                {uploading && <Loader2 className="h-4 w-4 animate-spin" />}
                {uploading ? 'Upload en cours...' : 'Uploader'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Enhanced Document Detail Modal with Analytics */}
      {showDocumentModal && selectedDocument && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-6xl w-full max-h-[90vh] overflow-y-auto">
            {/* Modal Header */}
            <div className="flex items-center justify-between p-6 border-b border-gray-200">
              <div className="flex items-center space-x-3">
                {getTypeIcon(selectedDocument.file_type)}
                <div>
                  <h3 className="text-xl font-semibold text-gray-900">{selectedDocument.title}</h3>
                  <p className="text-sm text-gray-600">{selectedDocument.document_type} • {selectedDocument.visibility}</p>
                </div>
              </div>
              <button
                onClick={closeDocumentModal}
                className="p-2 text-gray-400 hover:text-gray-600"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="p-6 space-y-6">
              {/* Document Info */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-4">
                  <h4 className="text-lg font-medium text-gray-900">Informations du document</h4>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">Taille:</span>
                      <span className="text-sm font-medium">{formatFileSize(selectedDocument.file_size)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">Uploadé le:</span>
                      <span className="text-sm font-medium">{formatDate(selectedDocument.uploaded_at)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">Statut:</span>
                      <div className="flex items-center space-x-1">
                        {getStatusIcon(selectedDocument.status)}
                        <span className="text-sm font-medium">{getStatusText(selectedDocument.status)}</span>
                      </div>
                    </div>
                    {selectedDocument.description && (
                      <div>
                        <span className="text-sm text-gray-600">Description:</span>
                        <p className="text-sm mt-1">{selectedDocument.description}</p>
                      </div>
                    )}
                    {selectedDocument.tags.length > 0 && (
                      <div>
                        <span className="text-sm text-gray-600">Tags:</span>
                        <div className="flex flex-wrap gap-1 mt-1">
                          {selectedDocument.tags.map((tag) => (
                            <span
                              key={tag}
                              className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-gray-100 text-gray-800"
                            >
                              <Tag className="h-3 w-3 mr-1" />
                              {tag}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>

                {/* Document Analytics */}
                <div className="space-y-4">
                  <h4 className="text-lg font-medium text-gray-900">Analytics du document</h4>
                  {analyticsLoading ? (
                    <div className="flex items-center justify-center py-8">
                      <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
                      <span className="ml-2 text-gray-600">Chargement des analytics...</span>
                    </div>
                  ) : documentAnalytics ? (
                    <div className="space-y-3">
                      <div className="grid grid-cols-2 gap-4">
                        <div className="bg-blue-50 p-3 rounded-lg">
                          <div className="flex items-center space-x-2">
                            <Activity className="h-5 w-5 text-blue-600" />
                            <div>
                              <p className="text-sm text-blue-600">Requêtes totales</p>
                              <p className="text-xl font-bold text-blue-900">
                                {documentAnalytics.current_query_count || 0}
                              </p>
                            </div>
                          </div>
                        </div>
                        <div className="bg-green-50 p-3 rounded-lg">
                          <div className="flex items-center space-x-2">
                            <TrendingUp className="h-5 w-5 text-green-600" />
                            <div>
                              <p className="text-sm text-green-600">Dernière utilisation</p>
                              <p className="text-sm font-medium text-green-900">
                                {documentAnalytics.last_accessed_at 
                                  ? formatDate(documentAnalytics.last_accessed_at)
                                  : 'Jamais'
                                }
                              </p>
                            </div>
                          </div>
                        </div>
                      </div>
                      
                      {documentAnalytics.detailed_records && documentAnalytics.detailed_records.length > 0 && (
                        <div className="bg-gray-50 p-3 rounded-lg">
                          <h5 className="text-sm font-medium text-gray-900 mb-2">Historique des 30 derniers jours</h5>
                          <div className="space-y-1">
                            {documentAnalytics.detailed_records.slice(0, 3).map((record: any, index: number) => (
                              <div key={index} className="flex justify-between text-xs">
                                <span className="text-gray-600">
                                  {formatDate(record.period_start)}
                                </span>
                                <span className="font-medium">
                                  {record.retrievals} requêtes
                                </span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  ) : (
                    <div className="text-center py-8 text-gray-500">
                      <BarChart3 className="h-12 w-12 mx-auto mb-2 text-gray-300" />
                      <p className="text-sm">Aucune donnée d'analytics disponible</p>
                    </div>
                  )}
                </div>
              </div>

              {/* Source Attribution Section */}
              <div className="border-t border-gray-200 pt-6">
                <h4 className="text-lg font-medium text-gray-900 mb-4">Source Attribution - Analyse d'utilisation</h4>
                <p className="text-sm text-gray-600 mb-4">
                  Testez une requête pour voir exactement quelles parties de ce document sont utilisées pour répondre aux questions.
                </p>
                
                <div className="space-y-4">
                  <div className="flex space-x-3">
                    <input
                      type="text"
                      value={sourceAttributionQuery}
                      onChange={(e) => setSourceAttributionQuery(e.target.value)}
                      placeholder="Ex: Quelles sont les exigences de sécurité pour les pesticides?"
                      className="flex-1 input"
                    />
                    <button
                      onClick={handleSourceAttribution}
                      disabled={!sourceAttributionQuery.trim() || attributionLoading}
                      className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                    >
                      {attributionLoading ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : (
                        <Target className="h-4 w-4" />
                      )}
                      Analyser
                    </button>
                  </div>

                  {sourceAttribution && (
                    <motion.div
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      className="bg-gray-50 rounded-lg p-4 space-y-4"
                    >
                      <div className="flex items-center space-x-2">
                        <Zap className="h-5 w-5 text-blue-600" />
                        <h5 className="font-medium text-gray-900">Résultats de l'analyse</h5>
                      </div>
                      
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div className="bg-white p-3 rounded-lg">
                          <p className="text-sm text-gray-600">Confiance globale</p>
                          <p className="text-xl font-bold text-blue-600">
                            {Math.round((sourceAttribution.overall_confidence || 0) * 100)}%
                          </p>
                        </div>
                        <div className="bg-white p-3 rounded-lg">
                          <p className="text-sm text-gray-600">Sources trouvées</p>
                          <p className="text-xl font-bold text-green-600">
                            {sourceAttribution.total_sources || 0}
                          </p>
                        </div>
                        <div className="bg-white p-3 rounded-lg">
                          <p className="text-sm text-gray-600">Requête</p>
                          <p className="text-sm font-medium text-gray-900 truncate">
                            "{sourceAttribution.query}"
                          </p>
                        </div>
                      </div>

                      {sourceAttribution.sources && sourceAttribution.sources.length > 0 && (
                        <div className="space-y-3">
                          <h6 className="font-medium text-gray-900">Sources utilisées:</h6>
                          {sourceAttribution.sources.map((source: any, index: number) => (
                            <div key={index} className="bg-white p-3 rounded-lg border">
                              <div className="flex items-start justify-between mb-2">
                                <div>
                                  <p className="font-medium text-sm">{source.filename}</p>
                                  <p className="text-xs text-gray-600">
                                    {source.page_info?.page_number && `Page ${source.page_info.page_number}`}
                                    {source.page_info?.section && ` • ${source.page_info.section}`}
                                  </p>
                                </div>
                                <div className="text-right">
                                  <p className="text-sm font-medium text-blue-600">
                                    {Math.round((source.relevance_score || 0) * 100)}%
                                  </p>
                                  <p className="text-xs text-gray-500">Pertinence</p>
                                </div>
                              </div>
                              <p className="text-sm text-gray-700 bg-gray-50 p-2 rounded">
                                {source.text_preview}
                              </p>
                            </div>
                          ))}
                        </div>
                      )}

                      {sourceAttribution.text_extracts && sourceAttribution.text_extracts.length > 0 && (
                        <div className="space-y-3">
                          <h6 className="font-medium text-gray-900">Extraits de texte pertinents:</h6>
                          {sourceAttribution.text_extracts.map((extract: any, index: number) => (
                            <div key={index} className="bg-white p-3 rounded-lg border">
                              <div className="space-y-2">
                                {extract.relevant_snippets && extract.relevant_snippets.map((snippet: string, snippetIndex: number) => (
                                  <p key={snippetIndex} className="text-sm text-gray-700 bg-blue-50 p-2 rounded">
                                    "{snippet}"
                                  </p>
                                ))}
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </motion.div>
                  )}
                </div>
              </div>

              {/* Chunk Analytics Section */}
              <div className="border-t border-gray-200 pt-6">
                <div className="flex items-center justify-between mb-4">
                  <h4 className="text-lg font-medium text-gray-900">Analytics des Chunks - Analyse Granulaire</h4>
                  <button
                    onClick={loadChunkAnalytics}
                    disabled={chunkAnalyticsLoading}
                    className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                  >
                    {chunkAnalyticsLoading ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <BarChart3 className="h-4 w-4" />
                    )}
                    {chunkAnalyticsLoading ? 'Chargement...' : 'Charger Analytics Chunks'}
                  </button>
                </div>
                
                <p className="text-sm text-gray-600 mb-4">
                  Analysez quels chunks de ce document sont les plus utilisés et performants.
                </p>

                {chunkAnalytics && (
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="bg-gray-50 rounded-lg p-4 space-y-4"
                  >
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                      <div className="bg-white p-3 rounded-lg">
                        <p className="text-sm text-gray-600">Total récupérations</p>
                        <p className="text-xl font-bold text-blue-600">
                          {chunkAnalytics.total_retrievals || 0}
                        </p>
                      </div>
                      <div className="bg-white p-3 rounded-lg">
                        <p className="text-sm text-gray-600">Chunks accédés</p>
                        <p className="text-xl font-bold text-green-600">
                          {chunkAnalytics.total_chunks_accessed || 0}
                        </p>
                      </div>
                      <div className="bg-white p-3 rounded-lg">
                        <p className="text-sm text-gray-600">Période analysée</p>
                        <p className="text-sm font-medium text-gray-900">
                          {chunkAnalytics.period_days} jours
                        </p>
                      </div>
                      <div className="bg-white p-3 rounded-lg">
                        <p className="text-sm text-gray-600">Document ID</p>
                        <p className="text-xs font-mono text-gray-500 truncate">
                          {chunkAnalytics.document_id}
                        </p>
                      </div>
                    </div>

                    {chunkAnalytics.chunk_statistics && chunkAnalytics.chunk_statistics.length > 0 && (
                      <div className="space-y-3">
                        <h6 className="font-medium text-gray-900">Statistiques par Chunk:</h6>
                        <div className="space-y-2 max-h-64 overflow-y-auto">
                          {chunkAnalytics.chunk_statistics.slice(0, 10).map((chunk: any, index: number) => (
                            <div key={index} className="bg-white p-3 rounded-lg border">
                              <div className="flex items-start justify-between mb-2">
                                <div className="flex-1">
                                  <div className="flex items-center space-x-2 mb-1">
                                    <span className="text-sm font-medium text-gray-900">
                                      Chunk {chunk.chunk_index}
                                    </span>
                                    <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">
                                      {chunk.retrieval_count} accès
                                    </span>
                                  </div>
                                  <p className="text-xs text-gray-600 mb-2">
                                    {chunk.content_preview}
                                  </p>
                                  {chunk.queries && chunk.queries.length > 0 && (
                                    <div className="text-xs text-gray-500">
                                      <span className="font-medium">Requêtes récentes:</span>
                                      <div className="mt-1 space-y-1">
                                        {chunk.queries.slice(0, 2).map((query: string, qIndex: number) => (
                                          <div key={qIndex} className="bg-gray-50 p-1 rounded text-xs">
                                            "{query.length > 50 ? query.substring(0, 50) + '...' : query}"
                                          </div>
                                        ))}
                                      </div>
                                    </div>
                                  )}
                                </div>
                                <div className="text-right ml-4">
                                  <p className="text-sm font-medium text-green-600">
                                    {Math.round((chunk.avg_relevance_score || 0) * 100)}%
                                  </p>
                                  <p className="text-xs text-gray-500">Pertinence</p>
                                  {chunk.last_accessed && (
                                    <p className="text-xs text-gray-400 mt-1">
                                      {formatDate(chunk.last_accessed)}
                                    </p>
                                  )}
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {chunkAnalytics.most_accessed_chunk && (
                      <div className="bg-blue-50 p-3 rounded-lg">
                        <h6 className="font-medium text-blue-900 mb-2">Chunk le plus utilisé</h6>
                        <p className="text-sm text-blue-800">
                          Chunk {chunkAnalytics.most_accessed_chunk.chunk_index} avec {chunkAnalytics.most_accessed_chunk.retrieval_count} accès
                        </p>
                        <p className="text-xs text-blue-600 mt-1">
                          {chunkAnalytics.most_accessed_chunk.content_preview}
                        </p>
                      </div>
                    )}
                  </motion.div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default DocumentsTab
