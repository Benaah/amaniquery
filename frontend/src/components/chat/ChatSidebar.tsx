"use client"

import { useState, useRef, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Plus, MessageSquare, Trash2, X, Pencil, Check, X as XIcon } from "lucide-react"
import type { ChatSession } from "./types"

interface ChatSidebarProps {
  chatHistory: ChatSession[]
  currentSessionId: string | null
  showHistory: boolean
  onLoadSession: (sessionId: string) => void
  onDeleteSession: (sessionId: string) => void
  onRenameSession: (sessionId: string, newTitle: string) => void
  onCreateSession: () => void
  onCloseHistory: () => void
}

export function ChatSidebar({
  chatHistory,
  currentSessionId,
  showHistory,
  onLoadSession,
  onDeleteSession,
  onRenameSession,
  onCreateSession,
  onCloseHistory
}: ChatSidebarProps) {
  const [editingSessionId, setEditingSessionId] = useState<string | null>(null)
  const [editTitle, setEditTitle] = useState("")
  const editInputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    if (editingSessionId && editInputRef.current) {
      editInputRef.current.focus()
    }
  }, [editingSessionId])

  const startEditing = (session: ChatSession, e: React.MouseEvent) => {
    e.stopPropagation()
    setEditingSessionId(session.id)
    setEditTitle(session.title || "")
  }

  const cancelEditing = (e?: React.MouseEvent) => {
    e?.stopPropagation()
    setEditingSessionId(null)
    setEditTitle("")
  }

  const saveTitle = (sessionId: string, e?: React.MouseEvent) => {
    e?.stopPropagation()
    if (editTitle.trim()) {
      onRenameSession(sessionId, editTitle.trim())
    }
    setEditingSessionId(null)
    setEditTitle("")
  }

  const handleKeyDown = (e: React.KeyboardEvent, sessionId: string) => {
    if (e.key === "Enter") {
      saveTitle(sessionId)
    } else if (e.key === "Escape") {
      cancelEditing()
    }
  }
  // Prevent body scroll when mobile sidebar is open
  useEffect(() => {
    if (showHistory) {
      document.body.style.overflow = "hidden"
    } else {
      document.body.style.overflow = "unset"
    }
    return () => {
      document.body.style.overflow = "unset"
    }
  }, [showHistory])

  return (
    <>
      {/* Desktop Sidebar */}
      <div className="hidden md:flex w-72 border-r border-sidebar-border bg-sidebar flex-col transition-all duration-300 ease-in-out h-full">
        <div className="p-4 border-b border-sidebar-border flex-shrink-0">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-sidebar-primary text-sidebar-primary-foreground flex items-center justify-center font-bold">
                A
              </div>
              <h3 className="font-semibold text-sm text-sidebar-foreground">AmaniQuery</h3>
            </div>
            <Button 
              variant="ghost" 
              size="sm" 
              onClick={onCreateSession} 
              className="h-8 w-8 rounded-full hover:bg-sidebar-accent hover:text-sidebar-accent-foreground"
            >
              <Plus className="w-4 h-4" />
            </Button>
          </div>
        </div>
        <div className="p-2 space-y-1 flex-1 overflow-y-auto [&::-webkit-scrollbar]:hidden [-ms-overflow-style:none] [scrollbar-width:none]">
          {chatHistory.map((session) => (
            <div key={session.id} className="flex items-center space-x-1 p-1 group min-w-0">
              <div
                className={cn(
                  "flex-1 flex items-center justify-between text-left h-auto px-3 py-2.5 text-sm transition-all duration-200 rounded-lg border border-transparent min-w-0 cursor-pointer",
                  currentSessionId === session.id 
                    ? "bg-sidebar-accent text-sidebar-accent-foreground font-medium" 
                    : "text-sidebar-foreground/80 hover:bg-sidebar-accent/50 hover:text-sidebar-foreground"
                )}
                onClick={() => onLoadSession(session.id)}
              >
                <div className="flex items-center w-full min-w-0 gap-3">
                  <MessageSquare className={cn(
                    "w-4 h-4 flex-shrink-0",
                    currentSessionId === session.id ? "text-sidebar-primary" : "text-muted-foreground"
                  )} />
                  <div className="flex-1 min-w-0 overflow-hidden">
                    {editingSessionId === session.id ? (
                      <div className="flex items-center gap-1" onClick={(e) => e.stopPropagation()}>
                        <Input
                          ref={editInputRef}
                          value={editTitle}
                          onChange={(e) => setEditTitle(e.target.value)}
                          onKeyDown={(e) => handleKeyDown(e, session.id)}
                          className="h-6 text-xs py-0 px-1 bg-background"
                        />
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-6 w-6 p-0 hover:text-green-500"
                          onClick={(e) => saveTitle(session.id, e)}
                        >
                          <Check className="w-3 h-3" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-6 w-6 p-0 hover:text-destructive"
                          onClick={cancelEditing}
                        >
                          <XIcon className="w-3 h-3" />
                        </Button>
                      </div>
                    ) : (
                      <>
                        <div 
                          className="truncate text-sm block"
                          title={session.title || `Chat ${session.id.slice(-6)}`}
                        >
                          {session.title || `Chat ${session.id.slice(-6)}`}
                        </div>
                      </>
                    )}
                  </div>
                </div>
              </div>
              <div className="flex flex-col gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity duration-200">
                <Button
                  variant="ghost"
                  size="sm"
                  className="text-muted-foreground hover:text-primary h-6 w-6 rounded-md p-0"
                  onClick={(e) => startEditing(session, e)}
                >
                  <Pencil className="w-3 h-3" />
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  className="text-muted-foreground hover:text-destructive h-6 w-6 rounded-md p-0"
                  onClick={(e) => {
                    e.stopPropagation()
                    onDeleteSession(session.id)
                  }}
                >
                  <Trash2 className="w-3 h-3" />
                </Button>
              </div>
            </div>
          ))}
        </div>
        
        {/* User Profile / Settings Area could go here */}
        <div className="p-4 border-t border-sidebar-border mt-auto">
             {/* Placeholder for settings if needed */}
        </div>
      </div>

      {/* Mobile Sidebar Overlay */}
      {showHistory && (
        <div className="md:hidden fixed inset-0 z-[60] bg-black/50 backdrop-blur-sm" onClick={onCloseHistory}>
          <div className="absolute left-0 top-0 h-full w-[85%] max-w-sm bg-sidebar border-r border-sidebar-border shadow-xl z-[61] flex flex-col" onClick={(e) => e.stopPropagation()}>
            <div className="p-4 border-b border-sidebar-border flex-shrink-0 flex items-center justify-between">
               <span className="font-semibold text-sidebar-foreground">Menu</span>
               <Button variant="ghost" size="sm" onClick={onCloseHistory}>
                  <X className="w-5 h-5" />
               </Button>
            </div>
            {/* Mobile list similar to desktop but adapted */}
            <div className="p-2 space-y-1 flex-1 overflow-y-auto">
                <Button onClick={() => { onCreateSession(); onCloseHistory(); }} className="w-full justify-start mb-4" variant="outline">
                    <Plus className="w-4 h-4 mr-2" /> New Chat
                </Button>
                {chatHistory.map((session) => (
                    <div key={session.id} onClick={() => { onLoadSession(session.id); onCloseHistory(); }} className="p-3 hover:bg-sidebar-accent rounded-lg cursor-pointer truncate text-sidebar-foreground">
                        {session.title || "New Chat"}
                    </div>
                ))}
            </div>
          </div>
        </div>
      )}
    </>
  )
}
