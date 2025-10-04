import React, { useState, useEffect } from 'react'
import { Outlet, NavLink, useNavigate, useLocation } from 'react-router-dom'
import { 
  Plus, 
  MessageCircle, 
  User, 
  Mic,
  BarChart3,
  Beaker,
  MapPin,
  Bell,
  TrendingUp
} from 'lucide-react'

// Components
import { ThemeToggle } from '@components/ThemeToggle'

// Hooks
import { useAuth } from '@hooks/useAuth'

interface NewLayoutProps {
  children?: React.ReactNode
}

const NewLayout: React.FC<NewLayoutProps> = ({ children }) => {
  const { user } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  
  // Check if we're on the Assistant page
  const isAssistantPage = location.pathname === '/assistant'

  const handleNewConversation = () => {
    // Navigate to assistant page to start a new conversation
    navigate('/assistant')
  }

  const handleChatClick = (chatId: string) => {
    // Navigate to assistant page with the specific conversation
    navigate(`/assistant?conversation=${chatId}`)
  }

  const navigation = [
    { name: 'Assistant', href: '/assistant', icon: MessageCircle },
    { name: 'Journal', href: '/journal', icon: Mic },
    { name: 'Activités', href: '/activities', icon: BarChart3 },
    { name: 'Traitements', href: '/treatments', icon: Beaker },
    { name: 'Parcelles', href: '/parcelles', icon: MapPin },
          { name: 'Knowledge Base', href: '/knowledge-base', icon: TrendingUp },
  ]

  // Real chat history from backend
  const [chatHistory, setChatHistory] = useState<Array<{
    id: string;
    title: string;
    time: string;
    active: boolean;
  }>>([])

  // Load real conversations from backend
  useEffect(() => {
    const loadConversations = async () => {
      try {
        const token = localStorage.getItem('auth_token')
        if (!token) return

        const response = await fetch('/api/v1/chat/conversations?limit=20', {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        })

        if (response.ok) {
          const conversations = await response.json()
          const formattedHistory = conversations.map((conv: any) => ({
            id: conv.id,
            title: conv.title,
            time: formatTimeAgo(new Date(conv.updated_at)),
            active: false // Will be set based on current route
          }))
          setChatHistory(formattedHistory)
        }
      } catch (error) {
        console.error('Error loading conversations:', error)
      }
    }

    if (user) {
      loadConversations()
    }
  }, [user])

  // Helper function to format time ago
  const formatTimeAgo = (date: Date): string => {
    const now = new Date()
    const diffInHours = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60))
    
    if (diffInHours < 1) return 'À l\'instant'
    if (diffInHours < 24) return `Il y a ${diffInHours}h`
    if (diffInHours < 48) return 'Hier'
    const diffInDays = Math.floor(diffInHours / 24)
    return `Il y a ${diffInDays} jours`
  }

  return (
    <div
      className="flex h-screen"
      style={{
        backgroundColor: 'var(--bg-app)',
        color: 'var(--text-primary)'
      }}
    >
      {/* Sidebar - Only show on Assistant page */}
      {isAssistantPage && (
        <div
          className="w-64 flex flex-col border-r pt-20"
          style={{
            borderColor: 'var(--border-subtle)'
          }}
        >
        {/* Smaller New Chat Button */}
        <div className="p-4">
          <button
            onClick={handleNewConversation}
            className="w-full py-2.5 px-4 rounded-lg text-sm font-medium transition-colors flex items-center justify-center gap-2"
            style={{
              backgroundColor: 'var(--brand-600)',
              color: 'var(--text-inverse)'
            }}
            onMouseEnter={(e) => e.currentTarget.style.backgroundColor = 'var(--brand-700)'}
            onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'var(--brand-600)'}
          >
            <Plus className="w-4 h-4" />
            Nouvelle conversation
          </button>
        </div>



        {/* Chat History */}
        <div className="flex-1 overflow-y-auto px-4">
          <h3
            className="text-xs uppercase tracking-wider mb-3"
            style={{ color: 'var(--text-muted)' }}
          >
            Conversations
          </h3>
          <div className="space-y-1">
            {chatHistory.map((chat) => (
              <div
                key={chat.id}
                onClick={() => handleChatClick(chat.id)}
                className="p-3 rounded-lg cursor-pointer transition-all duration-200"
                style={{
                  backgroundColor: chat.active ? 'rgba(255, 255, 255, 0.05)' : 'transparent',
                  color: chat.active ? 'var(--text-primary)' : 'var(--text-secondary)'
                }}
                onMouseEnter={(e) => {
                  if (!chat.active) {
                    e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.05)'
                  }
                }}
                onMouseLeave={(e) => {
                  if (!chat.active) {
                    e.currentTarget.style.backgroundColor = 'transparent'
                  }
                }}
              >
                <p className="text-sm font-medium truncate">{chat.title}</p>
                <p
                  className="text-xs"
                  style={{ color: 'var(--text-muted)' }}
                >
                  {chat.time}
                </p>
              </div>
            ))}
          </div>
        </div>

        {/* User profile at bottom */}
        <div className="p-4 border-t" style={{ borderColor: 'var(--border-subtle)' }}>
          <div className="flex items-center gap-3">
            <div
              className="w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium"
              style={{
                backgroundColor: 'var(--border-default)',
                color: 'var(--text-secondary)'
              }}
            >
              {user?.full_name?.charAt(0) || 'T'}
            </div>
            <div className="flex-1 min-w-0">
              <p
                className="text-sm font-medium truncate"
                style={{ color: 'var(--text-primary)' }}
              >
                {user?.full_name || 'Test Farmer'}
              </p>
              <p
                className="text-xs truncate"
                style={{ color: 'var(--text-muted)' }}
              >
                {user?.role === 'farmer' ? 'Agriculteur' : 'Utilisateur'}
              </p>
            </div>
          </div>
        </div>
        </div>
      )}

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col">
        {/* Header - Fixed, crosses entire width */}
        <header
          className="fixed top-0 left-0 right-0 border-b px-8 py-4 z-10"
          style={{
            backgroundColor: 'var(--bg-card)',
            borderColor: 'var(--border-subtle)'
          }}
        >
          <div className="flex items-center justify-between">
            {/* Left: Logo + Navigation */}
            <div className="flex items-center gap-8">
              <div className="flex items-center gap-3">
                <div
                  className="w-8 h-8 rounded flex items-center justify-center"
                  style={{ backgroundColor: 'var(--brand-600)' }}
                >
                  <span className="text-white font-bold text-sm">E</span>
                </div>
                <span
                  className="font-semibold text-xl"
                  style={{ color: 'var(--text-primary)' }}
                >
                  Ekumen
                </span>
              </div>

              <nav className="flex items-center gap-6">
                {navigation.map((item) => {
                  const Icon = item.icon
                  return (
                    <NavLink
                      key={item.name}
                      to={item.href}
                      className="flex items-center gap-2 px-3 py-2 rounded transition-colors"
                      style={({ isActive }) => ({
                        color: isActive ? 'var(--text-primary)' : 'var(--text-muted)'
                      })}
                      onMouseEnter={(e) => {
                        e.currentTarget.style.color = 'var(--text-primary)'
                      }}
                      onMouseLeave={(e) => {
                        const isActive = e.currentTarget.classList.contains('active')
                        e.currentTarget.style.color = isActive ? 'var(--text-primary)' : 'var(--text-muted)'
                      }}
                    >
                      <Icon className="w-4 h-4" />
                      {item.name}
                    </NavLink>
                  )
                })}
              </nav>
            </div>

            {/* Right: Theme Toggle + User Menu */}
            <div className="flex items-center gap-4">
              <ThemeToggle />
              
              <button
                className="p-2 rounded-lg transition-colors"
                style={{ color: 'var(--text-muted)' }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.color = 'var(--text-primary)'
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.color = 'var(--text-muted)'
                }}
              >
                <Bell className="w-5 h-5" />
              </button>

              <button
                className="p-2 rounded-lg transition-colors"
                style={{ color: 'var(--text-muted)' }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.color = 'var(--text-primary)'
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.color = 'var(--text-muted)'
                }}
              >
                <User className="w-5 h-5" />
              </button>
            </div>
          </div>
        </header>

        {/* Main Content - Add top margin for fixed header */}
        <main
          className="flex-1 overflow-y-auto pt-20"
          style={{ backgroundColor: 'var(--bg-app)' }}
        >
          {children || <Outlet />}
        </main>
      </div>
    </div>
  )
}

export default NewLayout
