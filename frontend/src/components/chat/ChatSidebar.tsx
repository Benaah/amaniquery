import { Button } from "@/components/ui/button"
import { Plus, MessageSquare, Trash2, X } from "lucide-react"
import type { ChatSession } from "./types"

interface ChatSidebarProps {
  chatHistory: ChatSession[]
  currentSessionId: string | null
  showHistory: boolean
  onLoadSession: (sessionId: string) => void
  onDeleteSession: (sessionId: string) => void
  onCreateSession: () => void
  onCloseHistory: () => void
}

export function ChatSidebar({
  chatHistory,
  currentSessionId,
  showHistory,
  onLoadSession,
  onDeleteSession,
  onCreateSession,
  onCloseHistory
}: ChatSidebarProps) {
  return (
    <>
      {/* Desktop Sidebar */}
      <div className="hidden md:flex w-72 border-r border-white/5 bg-black/20 backdrop-blur-xl overflow-y-auto flex-col transition-all duration-300 ease-in-out h-full [&::-webkit-scrollbar]:hidden [-ms-overflow-style:none] [scrollbar-width:none]">
        <div className="p-4 border-b border-white/5">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs uppercase tracking-widest text-muted-foreground">Sessions</p>
              <h3 className="font-semibold text-sm">Chat History</h3>
            </div>
            <Button variant="ghost" size="sm" onClick={onCreateSession} className="h-8 w-8 rounded-full">
              <Plus className="w-3 h-3" />
            </Button>
          </div>
          <div className="mt-3 rounded-xl border border-white/5 bg-white/5 px-3 py-2 text-xs text-muted-foreground">
            Quickly relive previous analyses or spin up a fresh thread.
          </div>
        </div>
        <div className="p-3 space-y-2 flex-1">
          {chatHistory.map((session) => (
            <div key={session.id} className="flex items-center space-x-2 p-1 group min-w-0">
              <Button
                variant={currentSessionId === session.id ? "secondary" : "ghost"}
                className="flex-1 justify-between text-left h-auto px-3 py-2 text-xs transition-all duration-200 rounded-2xl border border-transparent group-hover:border-white/10 min-w-0"
                onClick={() => onLoadSession(session.id)}
              >
                <div className="flex items-center w-full min-w-0">
                  <div className="flex h-7 w-7 items-center justify-center rounded-xl bg-white/10 mr-3 flex-shrink-0">
                    <MessageSquare className="w-3.5 h-3.5" />
                  </div>
                  <div className="flex-1 min-w-0 overflow-hidden">
                    <div 
                      className="font-medium truncate text-xs block"
                      title={session.title || `Chat ${session.id.slice(-6)}`}
                    >
                      {session.title || `Chat ${session.id.slice(-6)}`}
                    </div>
                    <div className="text-[11px] text-muted-foreground truncate">{session.message_count} messages</div>
                  </div>
                </div>
              </Button>
              <Button
                variant="ghost"
                size="sm"
                className="opacity-0 group-hover:opacity-100 text-muted-foreground hover:text-destructive h-7 w-7 rounded-full p-0 transition-opacity duration-200"
                onClick={(e) => {
                  e.stopPropagation()
                  onDeleteSession(session.id)
                }}
              >
                <Trash2 className="w-3.5 h-3.5" />
              </Button>
            </div>
          ))}
        </div>
      </div>

      {/* Mobile Sidebar Overlay */}
      {showHistory && (
        <div className="md:hidden fixed inset-0 z-50 bg-black/70 backdrop-blur-sm" onClick={onCloseHistory}>
          <div className="absolute left-0 top-0 h-full w-80 bg-background border-r border-white/10 shadow-2xl" onClick={(e) => e.stopPropagation()}>
            <div className="p-4 border-b border-white/10">
              <div className="flex items-center justify-between">
                <h3 className="font-semibold">Chat History</h3>
                <Button variant="ghost" size="sm" onClick={onCloseHistory}>
                  <X className="w-4 h-4" />
                </Button>
              </div>
              <Button
                variant="outline"
                size="sm"
                className="w-full mt-2 rounded-xl"
                onClick={() => {
                  onCreateSession()
                  onCloseHistory()
                }}
              >
                <Plus className="w-4 h-4 mr-2" />
                New Chat
              </Button>
            </div>
            <div className="p-2 space-y-1 flex-1 overflow-y-auto [&::-webkit-scrollbar]:hidden [-ms-overflow-style:none] [scrollbar-width:none]">
              {chatHistory.map((session) => (
                <div key={session.id} className="flex items-center space-x-2 p-1 group min-w-0">
                  <Button
                    variant={currentSessionId === session.id ? "secondary" : "ghost"}
                    className="flex-1 justify-start text-left h-auto p-3 min-w-0"
                    onClick={() => {
                      onLoadSession(session.id)
                      onCloseHistory()
                    }}
                  >
                    <MessageSquare className="w-4 h-4 mr-2 flex-shrink-0" />
                    <div className="flex-1 min-w-0 overflow-hidden">
                      <div 
                        className="font-medium truncate block"
                        title={session.title || `Chat ${session.id.slice(-8)}`}
                      >
                        {session.title || `Chat ${session.id.slice(-8)}`}
                      </div>
                      <div className="text-xs text-muted-foreground truncate">{session.message_count} messages</div>
                    </div>
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="text-muted-foreground hover:text-destructive"
                    onClick={(e) => {
                      e.stopPropagation()
                      onDeleteSession(session.id)
                    }}
                  >
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </>
  )
}
