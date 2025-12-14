"use client"

import { useState, useEffect } from "react"
import Link from "next/link"
import { usePathname, useRouter } from "next/navigation"
import { useAuth } from "@/lib/auth-context"
import { Button } from "./ui/button"
import { cn } from "@/lib/utils"
import type { ChatSession } from "./chat/types"
import {
  Home,
  MessageSquare,
  Mic,
  User,
  LogOut,
  Plus,
  Trash2,
  Pencil,
  Check,
  X,
  MoreVertical,
  Search,
  Clock,
  Star,
  Settings,
  ChevronRight,
  FileText,
  BarChart3
} from "lucide-react"
import "./sidebar.css"

interface AmaniSidebarProps {
  chatHistory: ChatSession[]
  currentSessionId: string | null
  onSessionSelect: (sessionId: string) => void
  onNewSession: () => void
  onDeleteSession: (sessionId: string) => void
  onRenameSession: (sessionId: string, newTitle: string) => void
  isOpen: boolean
  onToggle: () => void
}

export function AmaniSidebar({
  chatHistory,
  currentSessionId,
  onSessionSelect,
  onNewSession,
  onDeleteSession,
  onRenameSession,
  isOpen,
  onToggle
}: AmaniSidebarProps) {
  const [searchQuery, setSearchQuery] = useState("")
  const [editingSessionId, setEditingSessionId] = useState<string | null>(null)
  const [editTitle, setEditTitle] = useState("")
  const [showUserMenu, setShowUserMenu] = useState(false)
  const pathname = usePathname()
  const router = useRouter()
  const { user, logout } = useAuth()

  // Filter chat history based on search query
  const filteredHistory = chatHistory.filter(session =>
    (session.title || `Chat ${session.id.slice(-6)}`)
      .toLowerCase()
      .includes(searchQuery.toLowerCase())
  )

  // Navigation items
  const navItems = [
    { href: "/?noredirect=true", icon: Home, label: "Home", active: pathname === "/" },
    { href: "/chat", icon: MessageSquare, label: "Chat", active: pathname === "/chat" },
    { href: "/voice", icon: Mic, label: "Voice", active: pathname === "/voice" },
    { href: "/profile", icon: User, label: "Profile", active: pathname === "/profile" },
  ]

  const handleLogout = async () => {
    await logout()
    router.push("/")
  }

  const startEditing = (session: ChatSession) => {
    setEditingSessionId(session.id)
    setEditTitle(session.title || "")
  }

  const cancelEditing = () => {
    setEditingSessionId(null)
    setEditTitle("")
  }

  const saveTitle = (sessionId: string) => {
    if (editTitle.trim()) {
      onRenameSession(sessionId, editTitle.trim())
    }
    setEditingSessionId(null)
    setEditTitle("")
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    const now = new Date()
    const diffTime = Math.abs(now.getTime() - date.getTime())
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))
    
    if (diffDays === 1) return "Yesterday"
    if (diffDays < 7) return `${diffDays} days ago`
    if (diffDays < 30) return `${Math.floor(diffDays / 7)} weeks ago`
    return date.toLocaleDateString()
  }

  // Group sessions by date
  const groupedSessions = filteredHistory.reduce((groups, session) => {
    const date = new Date(session.updated_at)
    const today = new Date()
    const yesterday = new Date(today)
    yesterday.setDate(yesterday.getDate() - 1)
    
    let group = "Older"
    if (date.toDateString() === today.toDateString()) {
      group = "Today"
    } else if (date.toDateString() === yesterday.toDateString()) {
      group = "Yesterday"
    } else if (date.getTime() > today.getTime() - 7 * 24 * 60 * 60 * 1000) {
      group = "This Week"
    } else if (date.getTime() > today.getTime() - 30 * 24 * 60 * 60 * 1000) {
      group = "This Month"
    }
    
    if (!groups[group]) groups[group] = []
    groups[group].push(session)
    
    return groups
  }, {} as Record<string, ChatSession[]>)

  return (
    <div className="h-full flex">
      {/* Main Sidebar - Always visible on desktop */}
      <aside
        className={cn(
          "w-72 bg-card border-r flex flex-col transition-all duration-300 ease-in-out",
          "hidden md:flex", // Always show on desktop
          isOpen ? "w-80" : "w-72"
        )}
      >
        {/* Header */}
        <div className="p-4 border-b">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center">
                <MessageSquare className="w-4 h-4 text-primary" />
              </div>
              <div>
                <h1 className="text-lg font-semibold">AmaniQuery</h1>
                <p className="text-xs text-muted-foreground">AI Assistant</p>
              </div>
            </div>
            <Button
              variant="ghost"
              size="sm"
              className="h-8 w-8 p-0"
              onClick={onToggle}
            >
              <ChevronRight className={cn("w-4 h-4 transition-transform", isOpen && "rotate-180")} />
            </Button>
          </div>

          {/* Search */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <input
              type="text"
              placeholder="Search conversations..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-3 py-2 bg-background border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>
        </div>

        {/* Navigation */}
        <nav className="p-2 border-b">
          {navItems.map((item) => {
            const Icon = item.icon
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors text-sm",
                  item.active
                    ? "bg-primary/10 text-primary font-medium"
                    : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
                )}
              >
                <Icon className="w-4 h-4" />
                <span>{item.label}</span>
              </Link>
            )
          })}
        </nav>

        {/* Chat History */}
        <div className="flex-1 overflow-y-auto custom-scrollbar">
          <div className="p-4">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-medium text-muted-foreground">Recent Chats</h3>
              <Button
                variant="ghost"
                size="sm"
                className="h-6 w-6 p-0"
                onClick={onNewSession}
              >
                <Plus className="w-3 h-3" />
              </Button>
            </div>

            {chatHistory.length === 0 ? (
              <div className="text-center py-8">
                <MessageSquare className="w-8 h-8 text-muted-foreground mx-auto mb-2" />
                <p className="text-sm text-muted-foreground">No conversations yet</p>
                <Button
                  variant="outline"
                  size="sm"
                  className="mt-3"
                  onClick={onNewSession}
                >
                  Start New Chat
                </Button>
              </div>
            ) : (
              <div className="space-y-4">
                {Object.entries(groupedSessions).map(([group, sessions]) => (
                  <div key={group}>
                    <h4 className="text-xs font-medium text-muted-foreground mb-2 px-1">
                      {group}
                    </h4>
                    <div className="space-y-1">
                      {sessions.map((session) => (
                        <div
                          key={session.id}
                          className={cn(
                            "group relative rounded-lg transition-colors",
                            currentSessionId === session.id
                              ? "bg-primary/10 text-primary"
                              : "hover:bg-accent hover:text-accent-foreground"
                          )}
                        >
                          <div
                            className="flex items-center gap-3 p-3 cursor-pointer"
                            onClick={() => onSessionSelect(session.id)}
                          >
                            <div className="flex-1 min-w-0">
                              {editingSessionId === session.id ? (
                                <div className="flex items-center gap-2">
                                  <input
                                    type="text"
                                    value={editTitle}
                                    onChange={(e) => setEditTitle(e.target.value)}
                                    onKeyDown={(e) => {
                                      if (e.key === "Enter") saveTitle(session.id)
                                      if (e.key === "Escape") cancelEditing()
                                    }}
                                    className="flex-1 px-2 py-1 text-sm bg-background border rounded"
                                    autoFocus
                                  />
                                  <Button
                                    variant="ghost"
                                    size="sm"
                                    className="h-6 w-6 p-0"
                                    onClick={() => saveTitle(session.id)}
                                  >
                                    <Check className="w-3 h-3" />
                                  </Button>
                                  <Button
                                    variant="ghost"
                                    size="sm"
                                    className="h-6 w-6 p-0"
                                    onClick={cancelEditing}
                                  >
                                    <X className="w-3 h-3" />
                                  </Button>
                                </div>
                              ) : (
                                <>
                                  <div
                                    className="text-sm font-medium truncate"
                                    title={session.title || `Chat ${session.id.slice(-6)}`}
                                  >
                                    {session.title || `Chat ${session.id.slice(-6)}`}
                                  </div>
                                  <div className="flex items-center gap-2 text-xs text-muted-foreground">
                                    <Clock className="w-3 h-3" />
                                    <span>{formatDate(session.updated_at)}</span>
                                    <span>•</span>
                                    <span>{session.message_count} messages</span>
                                  </div>
                                </>
                              )}
                            </div>
                          </div>
                          
                          {/* Action buttons - appear on hover */}
                          <div className="absolute right-2 top-1/2 transform -translate-y-1/2 opacity-0 group-hover:opacity-100 transition-opacity">
                            <div className="flex items-center gap-1">
                              <Button
                                variant="ghost"
                                size="sm"
                                className="h-6 w-6 p-0"
                                onClick={(e) => {
                                  e.stopPropagation()
                                  startEditing(session)
                                }}
                              >
                                <Pencil className="w-3 h-3" />
                              </Button>
                              <Button
                                variant="ghost"
                                size="sm"
                                className="h-6 w-6 p-0 text-muted-foreground hover:text-destructive"
                                onClick={(e) => {
                                  e.stopPropagation()
                                  onDeleteSession(session.id)
                                }}
                              >
                                <Trash2 className="w-3 h-3" />
                              </Button>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="p-4 border-t">
          {user && (
            <div className="relative mb-3">
              <button
                className="w-full flex items-center gap-3 p-2 rounded-lg hover:bg-accent transition-colors"
                onClick={() => setShowUserMenu(!showUserMenu)}
              >
                {user.profile_image_url ? (
                  <div className="w-8 h-8 rounded-full overflow-hidden flex-shrink-0">
                    <img
                      src={user.profile_image_url}
                      alt={user.name || "Profile"}
                      className="w-full h-full object-cover"
                    />
                  </div>
                ) : (
                  <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
                    <User className="w-4 h-4 text-primary" />
                  </div>
                )}
                <div className="flex-1 min-w-0 text-left">
                  <p className="text-sm font-medium truncate">{user.name || "User"}</p>
                  <p className="text-xs text-muted-foreground truncate">{user.email}</p>
                </div>
                <MoreVertical className="w-4 h-4 text-muted-foreground" />
              </button>

              {/* User Dropdown Menu */}
              {showUserMenu && (
                <div className="absolute bottom-full left-0 right-0 mb-2 bg-popover border rounded-lg shadow-lg py-1 z-50">
                  <Link
                    href="/profile"
                    className="flex items-center gap-2 px-3 py-2 text-sm hover:bg-accent hover:text-accent-foreground transition-colors"
                    onClick={() => setShowUserMenu(false)}
                  >
                    <User className="w-4 h-4" />
                    Profile
                  </Link>
                  <button
                    className="w-full flex items-center gap-2 px-3 py-2 text-sm hover:bg-accent hover:text-accent-foreground transition-colors text-destructive"
                    onClick={() => {
                      setShowUserMenu(false)
                      handleLogout()
                    }}
                  >
                    <LogOut className="w-4 h-4" />
                    Logout
                  </button>
                </div>
              )}
            </div>
          )}

          <Button
            variant="outline"
            className="w-full justify-start text-sm"
            onClick={handleLogout}
          >
            <LogOut className="w-4 h-4 mr-2" />
            Sign Out
          </Button>
        </div>
      </aside>

      {/* Mobile Sidebar Overlay */}
      <div className="md:hidden">
        {isOpen && (
          <div className="fixed inset-0 z-[60] bg-black/70 backdrop-blur-sm" onClick={onToggle}>
            <div 
              className="absolute left-0 top-0 h-full w-[85%] max-w-sm bg-card border-r shadow-2xl z-[61] flex flex-col" 
              onClick={(e) => e.stopPropagation()}
            >
              {/* Mobile content would go here - simplified for mobile */}
              <div className="p-4 border-b">
                <div className="flex items-center justify-between mb-4">
                  <h1 className="text-lg font-semibold">AmaniQuery</h1>
                  <Button variant="ghost" size="sm" onClick={onToggle}>
                    <X className="w-4 h-4" />
                  </Button>
                </div>
                <input
                  type="text"
                  placeholder="Search conversations..."
                  className="w-full px-3 py-2 bg-background border rounded-lg text-sm"
                />
              </div>
              <div className="flex-1 overflow-y-auto p-4">
                {chatHistory.map((session) => (
                  <button
                    key={session.id}
                    className={cn(
                      "w-full text-left p-3 rounded-lg mb-2 transition-colors",
                      currentSessionId === session.id
                        ? "bg-primary/10 text-primary"
                        : "hover:bg-accent"
                    )}
                    onClick={() => {
                      onSessionSelect(session.id)
                      onToggle()
                    }}
                  >
                    <div className="font-medium text-sm truncate">
                      {session.title || `Chat ${session.id.slice(-6)}`}
                    </div>
                    <div className="text-xs text-muted-foreground">
                      {session.message_count} messages
                    </div>
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}