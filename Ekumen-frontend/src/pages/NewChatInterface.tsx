import React, { useState } from 'react'
import { Send, Paperclip, Mic, FileText, Activity, Shield, TrendingUp } from 'lucide-react'

const NewChatInterface: React.FC = () => {
  const [inputValue, setInputValue] = useState('')
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null)

  const categories = [
    {
      id: 'farm-data',
      title: 'Données d\'Exploitation',
      icon: FileText,
      description: 'Analyse de parcelles et interventions',
      color: 'var(--brand-600)'
    },
    {
      id: 'weather',
      title: 'Météorologie',
      icon: Activity,
      description: 'Prévisions et fenêtres d\'intervention',
      color: '#3b82f6'
    },
    {
      id: 'health-compliance',
      title: 'Santé des Cultures',
      icon: Shield,
      description: 'Diagnostic et protection',
      color: '#f59e0b'
    },
    {
      id: 'market-suppliers',
      title: 'Marché & Fournisseurs',
      icon: TrendingUp,
      description: 'Prix et recherche',
      color: '#8b5cf6'
    }
  ]

  const handleCategoryClick = (categoryId: string) => {
    setSelectedCategory(categoryId)
    // Here you would trigger the appropriate agent
  }

  const handleSendMessage = () => {
    if (!inputValue.trim()) return
    
    // Handle message sending logic here
    console.log('Sending message:', inputValue)
    setInputValue('')
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  return (
    <div 
      className="h-full flex flex-col"
      style={{ 
        backgroundColor: 'var(--bg-app)', 
        color: 'var(--text-primary)'
      }}
    >
      {/* Main Content Area - Clean ChatGPT-like Interface */}
      <div className="flex-1 flex items-center justify-center px-8">
        <div className="w-full max-w-3xl text-center">
          {/* Welcome Message */}
          <div className="mb-16">
            <h1
              className="text-3xl font-light mb-6"
              style={{ color: 'var(--text-primary)' }}
            >
              Assistant Agricole Ekumen
            </h1>
            <p
              className="text-lg"
              style={{ color: 'var(--text-muted)' }}
            >
              Posez votre question agricole
            </p>
          </div>

          {/* Main Input Card - Drastically Increased Height */}
          <div
            className="rounded-2xl border mb-8 shadow-lg"
            style={{
              backgroundColor: 'var(--bg-input)',
              borderColor: 'var(--border-default)'
            }}
          >
            {/* Input Area - Much Taller */}
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
              />

              {/* Right side controls - Positioned in top right */}
              <div className="absolute right-4 top-4 flex items-center gap-2">
                <button
                  className="p-2 rounded-lg transition-colors"
                  style={{ color: 'var(--text-muted)' }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.color = 'var(--text-primary)'
                    e.currentTarget.style.backgroundColor = 'var(--bg-card-hover)'
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.color = 'var(--text-muted)'
                    e.currentTarget.style.backgroundColor = 'transparent'
                  }}
                >
                  <Paperclip className="w-4 h-4" />
                </button>
                <button
                  className="p-2 rounded-lg transition-colors"
                  style={{ color: 'var(--text-muted)' }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.color = 'var(--text-primary)'
                    e.currentTarget.style.backgroundColor = 'var(--bg-card-hover)'
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.color = 'var(--text-muted)'
                    e.currentTarget.style.backgroundColor = 'transparent'
                  }}
                >
                  <Mic className="w-4 h-4" />
                </button>
                <button
                  onClick={handleSendMessage}
                  disabled={!inputValue.trim()}
                  className="p-3 rounded-xl transition-colors ml-1 disabled:opacity-50 disabled:cursor-not-allowed"
                  style={{
                    backgroundColor: 'var(--brand-600)',
                    color: 'var(--text-inverse)'
                  }}
                  onMouseEnter={(e) => {
                    if (!e.currentTarget.disabled) {
                      e.currentTarget.style.backgroundColor = 'var(--brand-700)'
                    }
                  }}
                  onMouseLeave={(e) => {
                    if (!e.currentTarget.disabled) {
                      e.currentTarget.style.backgroundColor = 'var(--brand-600)'
                    }
                  }}
                >
                  <Send className="w-4 h-4" />
                </button>
              </div>
            </div>

            {/* Mode Buttons at Bottom of Card */}
            <div
              className="flex items-center gap-3 px-6 py-4 border-t"
              style={{ borderColor: 'var(--border-subtle)' }}
            >
              <button
                className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm transition-colors border"
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
              >
                <span>Mode Fournisseurs</span>
              </button>
              <button
                className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm transition-colors border"
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
              >
                <span>Mode Internet</span>
              </button>
            </div>
          </div>

          {/* Popular Suggestions Below Input */}
          <div className="text-center">
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
        </div>
      </div>


    </div>
  )
}

export default NewChatInterface
