import { useState, useRef, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Badge } from "@/components/ui/badge"
import { Paperclip, Mic, Send, Loader2, Search, Sparkles } from "lucide-react"
import { FileUpload } from "./FileUpload"

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
  setShowAutocomplete
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

  return (
    <div className="border-t border-white/5 bg-background/80 p-2 md:p-3 flex-shrink-0">
      <form onSubmit={handleSubmit} className="space-y-1.5">
        <div className="flex items-center justify-between text-[10px] md:text-xs text-muted-foreground px-1 mb-1">
          <div className="flex items-center gap-1 md:gap-1.5 min-w-0 flex-1">
            <Sparkles className="w-3 h-3 text-primary animate-pulse flex-shrink-0" />
            <span className="hidden sm:inline truncate">
              {isResearchMode
                ? "Agentic research mode with multi-stage reasoning & tool use"
                : useHybrid
                ? "Hybrid RAG with enhanced retrieval"
                : "Chat mode delivers fast summaries with citations"}
            </span>
            <span className="sm:hidden truncate">
              {isResearchMode ? "Agentic Research" : useHybrid ? "Hybrid RAG" : "Chat"}
            </span>
          </div>
          <div className="flex items-center gap-1.5 md:gap-2 flex-shrink-0">
            {isResearchMode && (
              <Badge variant="secondary" className="text-[9px] md:text-[10px] px-1 md:px-1.5 py-0.5">
                <Sparkles className="w-2 h-2 md:w-2.5 md:h-2.5 mr-0.5 md:mr-1" />
                <span className="hidden xs:inline">Agentic</span>
              </Badge>
            )}
            {useHybrid && (
              <Badge variant="outline" className="text-[9px] md:text-[10px] px-1 md:px-1.5 py-0.5">
                <span className="hidden xs:inline">Hybrid</span>
              </Badge>
            )}
            <span className={`text-[9px] md:text-[10px] transition-colors whitespace-nowrap ${isLoading ? "text-primary animate-pulse" : ""}`}>
              {isLoading ? "Streaming..." : "Ready"}
            </span>
          </div>
        </div>
        {selectedFiles.length > 0 && (
          <div className="mb-2 px-1 md:px-2">
            <FileUpload
              files={selectedFiles}
              onFilesChange={setSelectedFiles}
              maxFiles={5}
              maxSizeMB={10}
            />
          </div>
        )}
        <div className="rounded-2xl border border-white/10 bg-white/5 px-2 md:px-3 py-2 shadow-lg backdrop-blur-lg">
          <div className="flex items-end gap-1.5 md:gap-2">
            <div className="flex items-center gap-0.5 md:gap-1 flex-shrink-0">
              <Button
                variant="ghost"
                size="icon"
                type="button"
                className="h-11 w-11 md:h-8 md:w-8 rounded-xl text-muted-foreground"
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
                <Paperclip className="w-4 h-4 md:w-3.5 md:h-3.5" />
              </Button>
              <Button variant="ghost" size="icon" type="button" className="h-11 w-11 md:h-8 md:w-8 rounded-xl text-muted-foreground">
                <Mic className="w-4 h-4 md:w-3.5 md:h-3.5" />
              </Button>
            </div>
            <div className="relative flex-1 min-w-0">
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
                  // Enter to send, Shift+Enter for new line
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
                  // Delay hiding to allow clicking on suggestions
                  if (setShowAutocomplete) {
                    setTimeout(() => setShowAutocomplete(false), 200)
                  }
                }}
                placeholder={
                  isResearchMode
                    ? "Ask detailed legal research questions about Kenyan laws..."
                    : "Ask about Kenyan law, parliament, or news..."
                }
                className="w-full border-0 bg-transparent text-sm md:text-base focus-visible:ring-0 py-2 md:py-2 resize-none min-h-[44px] max-h-[200px] overflow-y-auto [&::-webkit-scrollbar]:hidden [-ms-overflow-style:none] [scrollbar-width:none]"
                disabled={isLoading}
                rows={1}
              />
              {enableAutocomplete && showAutocomplete && autocompleteSuggestions.length > 0 && (
                <div className="absolute bottom-full left-0 right-0 mb-1 rounded-xl border border-white/10 bg-white/95 dark:bg-gray-900/95 backdrop-blur-lg shadow-xl z-[100] max-h-48 md:max-h-60 overflow-y-auto [&::-webkit-scrollbar]:hidden [-ms-overflow-style:none] [scrollbar-width:none]">
                  {autocompleteSuggestions.map((suggestion, idx) => (
                    <button
                      key={idx}
                      type="button"
                      onMouseDown={(e) => {
                        // Prevent input blur when clicking
                        e.preventDefault()
                        setInput(suggestion)
                        if (setShowAutocomplete) setShowAutocomplete(false)
                        inputRef.current?.focus()
                      }}
                      className="w-full px-3 md:px-4 py-2.5 md:py-2 text-left text-sm hover:bg-primary/10 dark:hover:bg-primary/20 transition-colors first:rounded-t-xl last:rounded-b-xl text-foreground min-h-[44px] flex items-center"
                    >
                      <div className="flex items-center gap-2">
                        <Search className="w-3.5 h-3.5 text-muted-foreground flex-shrink-0" />
                        <span className="truncate">{suggestion}</span>
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </div>
            <Button type="submit" disabled={isLoading || (!input.trim() && selectedFiles.length === 0)} className="h-11 w-11 md:h-9 md:w-9 rounded-xl flex-shrink-0">
              {isLoading ? <Loader2 className="w-4 h-4 md:w-3.5 md:h-3.5 animate-spin" /> : <Send className="w-4 h-4 md:w-3.5 md:h-3.5" />}
            </Button>
          </div>
        </div>
      </form>
    </div>
  )
}
