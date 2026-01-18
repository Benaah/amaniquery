import { useState, useRef, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Badge } from "@/components/ui/badge"
import { Paperclip, Mic, Send, Loader2, Search, Sparkles } from "lucide-react"
import { FileUpload } from "./FileUpload"

import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { ChevronDown, MessageSquare } from "lucide-react"

interface ChatInputProps {
  input: string
  setInput: (value: string) => void
  isLoading: boolean
  isResearchMode: boolean
  useHybrid: boolean
  selectedFiles: File[]
  setSelectedFiles: React.Dispatch<React.SetStateAction<File[]>>
  onSendMessage: (content: string) => void
  enableAutocomplete?: boolean
  autocompleteSuggestions?: string[]
  showAutocomplete?: boolean
  setShowAutocomplete?: (show: boolean) => void
  onToggleResearch: () => void
  onToggleHybrid: () => void
}

export function ChatInput({
  input,
  setInput,
  isLoading,
  isResearchMode,
  useHybrid,
  selectedFiles,
  setSelectedFiles,
  onSendMessage,
  enableAutocomplete = true,
  autocompleteSuggestions = [],
  showAutocomplete = false,
  setShowAutocomplete,
  onToggleResearch,
  onToggleHybrid
}: ChatInputProps) {
  const inputRef = useRef<HTMLTextAreaElement | null>(null)
  const textareaRef = useRef<HTMLTextAreaElement | null>(null)

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto"
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`
    }
  }, [input])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (input.trim() || selectedFiles.length > 0) {
      onSendMessage(input)
    }
  }

  const getCurrentMode = () => {
    if (isResearchMode) return { label: "Research", icon: Search, color: "text-blue-500" }
    if (useHybrid) return { label: "Hybrid", icon: Sparkles, color: "text-purple-500" }
    return { label: "Chat", icon: MessageSquare, color: "text-muted-foreground" }
  }

  const currentMode = getCurrentMode()
  const ModeIcon = currentMode.icon

  return (
    <div className="p-4 flex-shrink-0 z-20">
      <div className="max-w-3xl mx-auto">
        <form onSubmit={handleSubmit} className="relative">
          {selectedFiles.length > 0 && (
            <div className="mb-2 px-1">
              <FileUpload
                files={selectedFiles}
                onFilesChange={setSelectedFiles}
                maxFiles={5}
                maxSizeMB={10}
              />
            </div>
          )}
          
          <div className="relative flex flex-col gap-2 rounded-3xl border shadow-sm bg-secondary/50 focus-within:ring-1 focus-within:ring-ring transition-all duration-200 overflow-hidden px-4 py-3">
            <div className="flex-1 min-w-0">
              <Textarea
                ref={(el) => {
                  inputRef.current = el
                  textareaRef.current = el
                }}
                value={input}
                onChange={(e) => {
                  setInput(e.target.value)
                  if (enableAutocomplete && setShowAutocomplete) {
                    setShowAutocomplete(true)
                  }
                }}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault()
                    if ((input.trim() || selectedFiles.length > 0) && !isLoading) {
                      onSendMessage(input)
                    }
                  }
                }}
                onFocus={() => {
                  if (enableAutocomplete && autocompleteSuggestions.length > 0 && setShowAutocomplete) {
                    setShowAutocomplete(true)
                  }
                }}
                onBlur={() => {
                  if (setShowAutocomplete) {
                    setTimeout(() => setShowAutocomplete(false), 200)
                  }
                }}
                placeholder={
                  isResearchMode
                    ? "Deep research mode enabled..."
                    : "Send a message..."
                }
                className="w-full border-0 bg-transparent text-sm md:text-base focus-visible:ring-0 p-0 resize-none min-h-[24px] max-h-[200px] overflow-y-auto shadow-none text-foreground placeholder:text-muted-foreground leading-relaxed"
                disabled={isLoading}
                rows={1}
              />
              
              {enableAutocomplete && showAutocomplete && autocompleteSuggestions.length > 0 && (
                <div className="absolute bottom-full left-0 right-0 mb-2 rounded-2xl border bg-popover shadow-xl z-[100] max-h-60 overflow-y-auto overflow-hidden">
                  {autocompleteSuggestions.map((suggestion, idx) => (
                    <button
                      key={idx}
                      type="button"
                      onMouseDown={(e) => {
                        e.preventDefault()
                        setInput(suggestion)
                        if (setShowAutocomplete) setShowAutocomplete(false)
                        inputRef.current?.focus()
                      }}
                      className="w-full px-4 py-2.5 text-left text-sm hover:bg-muted transition-colors text-foreground flex items-center gap-2"
                    >
                      <Search className="w-3.5 h-3.5 text-muted-foreground flex-shrink-0" />
                      <span className="truncate">{suggestion}</span>
                    </button>
                  ))}
                </div>
              )}
            </div>

            <div className="flex items-center justify-between pt-2 border-t border-border/50">
              <div className="flex items-center gap-1">
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-8 gap-1.5 px-2 text-xs font-medium text-muted-foreground hover:text-foreground hover:bg-background/50 rounded-lg"
                    >
                      <ModeIcon className={`w-3.5 h-3.5 ${currentMode.color}`} />
                      <span className="hidden sm:inline">{currentMode.label}</span>
                      <ChevronDown className="w-3 h-3 opacity-50" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="start" className="w-48">
                    <DropdownMenuItem onClick={() => {
                      if (isResearchMode) onToggleResearch()
                      if (useHybrid) onToggleHybrid()
                    }}>
                      <MessageSquare className="w-4 h-4 mr-2" />
                      Standard Chat
                    </DropdownMenuItem>
                    <DropdownMenuItem onClick={() => {
                      if (isResearchMode) onToggleResearch()
                      if (!useHybrid) onToggleHybrid()
                    }}>
                      <Sparkles className="w-4 h-4 mr-2 text-purple-500" />
                      Hybrid RAG
                    </DropdownMenuItem>
                    <DropdownMenuItem onClick={() => {
                      if (!isResearchMode) onToggleResearch()
                      if (useHybrid) onToggleHybrid()
                    }}>
                      <Search className="w-4 h-4 mr-2 text-blue-500" />
                      Agentic Research
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>

                <Button
                  variant="ghost"
                  size="icon"
                  type="button"
                  className="h-8 w-8 rounded-lg text-muted-foreground hover:bg-background/50"
                  onClick={() => {
                    const input = document.createElement("input")
                    input.type = "file"
                    input.multiple = true
                    input.accept = ".pdf,.png,.jpg,.jpeg,.txt,.md"
                    input.onchange = (e) => {
                      const files = (e.target as HTMLInputElement).files
                      if (files) {
                        setSelectedFiles(prev => [...prev, ...Array.from(files)].slice(0, 5))
                      }
                    }
                    input.click()
                  }}
                >
                  <Paperclip className="w-4 h-4" />
                </Button>
              </div>

              <Button 
                type="submit" 
                disabled={isLoading || (!input.trim() && selectedFiles.length === 0)} 
                className={cn(
                  "h-8 w-8 rounded-lg flex-shrink-0 transition-all duration-200",
                  (input.trim() || selectedFiles.length > 0) 
                    ? "bg-primary text-primary-foreground hover:opacity-90" 
                    : "bg-muted text-muted-foreground hover:bg-muted"
                )}
                size="icon"
              >
                {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
              </Button>
            </div>
          </div>
        </form>
        <div className="text-center mt-2">
            <p className="text-[10px] text-muted-foreground">AmaniQuery can make mistakes. Consider checking important information.</p>
        </div>
      </div>
    </div>
  )
}
