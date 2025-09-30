import React, { useState } from 'react'
import { ExternalLink, ChevronDown, ChevronUp, Globe, Database, FileText, Zap } from 'lucide-react'

interface Source {
  title: string
  url: string
  snippet?: string
  relevance?: number
  type?: 'web' | 'database' | 'document' | 'api'
}

interface SourcesProps {
  sources: Source[]
}

const Sources: React.FC<SourcesProps> = ({ sources }) => {
  const [isExpanded, setIsExpanded] = useState(false)

  if (!sources || sources.length === 0) {
    return null
  }

  const getSourceIcon = (type?: string) => {
    switch (type) {
      case 'web':
        return <Globe className="h-4 w-4 text-blue-500" />
      case 'database':
        return <Database className="h-4 w-4 text-green-500" />
      case 'document':
        return <FileText className="h-4 w-4 text-purple-500" />
      case 'api':
        return <Zap className="h-4 w-4 text-yellow-500" />
      default:
        return <Globe className="h-4 w-4 text-gray-500" />
    }
  }

  const getRelevanceColor = (relevance?: number) => {
    if (!relevance) return 'bg-gray-200'
    if (relevance >= 0.8) return 'bg-green-500'
    if (relevance >= 0.6) return 'bg-yellow-500'
    return 'bg-orange-500'
  }

  const displayedSources = isExpanded ? sources : sources.slice(0, 3)

  return (
    <div className="mt-4 border-t border-gray-200 pt-3">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <ExternalLink className="h-4 w-4 text-gray-500" />
          <span className="text-sm font-medium text-gray-700">
            Sources ({sources.length})
          </span>
        </div>
        {sources.length > 3 && (
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="flex items-center gap-1 text-xs text-primary-600 hover:text-primary-700 transition-colors"
          >
            {isExpanded ? (
              <>
                Voir moins <ChevronUp className="h-3 w-3" />
              </>
            ) : (
              <>
                Voir tout ({sources.length}) <ChevronDown className="h-3 w-3" />
              </>
            )}
          </button>
        )}
      </div>

      <div className="space-y-2">
        {displayedSources.map((source, index) => (
          <a
            key={index}
            href={source.url}
            target="_blank"
            rel="noopener noreferrer"
            className="block p-3 bg-gray-50 hover:bg-gray-100 rounded-lg transition-colors group"
          >
            <div className="flex items-start gap-3">
              <div className="flex-shrink-0 mt-0.5">
                {getSourceIcon(source.type)}
              </div>
              
              <div className="flex-1 min-w-0">
                <div className="flex items-start justify-between gap-2">
                  <h4 className="text-sm font-medium text-gray-900 group-hover:text-primary-600 transition-colors line-clamp-1">
                    {source.title}
                  </h4>
                  {source.relevance !== undefined && (
                    <div className="flex items-center gap-1 flex-shrink-0">
                      <div className={`h-2 w-2 rounded-full ${getRelevanceColor(source.relevance)}`} />
                      <span className="text-xs text-gray-500">
                        {Math.round(source.relevance * 100)}%
                      </span>
                    </div>
                  )}
                </div>
                
                {source.snippet && (
                  <p className="text-xs text-gray-600 mt-1 line-clamp-2">
                    {source.snippet}
                  </p>
                )}
                
                <div className="flex items-center gap-2 mt-2">
                  <span className="text-xs text-gray-500 truncate">
                    {new URL(source.url).hostname}
                  </span>
                  <ExternalLink className="h-3 w-3 text-gray-400 group-hover:text-primary-500 transition-colors flex-shrink-0" />
                </div>
              </div>
            </div>
          </a>
        ))}
      </div>

      {sources.length > 3 && !isExpanded && (
        <button
          onClick={() => setIsExpanded(true)}
          className="w-full mt-2 py-2 text-xs text-gray-600 hover:text-gray-800 hover:bg-gray-50 rounded transition-colors"
        >
          + {sources.length - 3} autres sources
        </button>
      )}
    </div>
  )
}

export default Sources

