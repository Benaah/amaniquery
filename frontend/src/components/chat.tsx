"use client"

import { useState, useEffect, useCallback, useRef } from "react"
import { toast } from "sonner"
import {
  ChatSidebar
} from "./chat/ChatSidebar"
import { ChatHeader } from "./chat/ChatHeader"
import { ChatInput } from "./chat/ChatInput"
import { MessageList } from "./chat/MessageList"
import type {
  Message,
  ChatSession,
  StreamMetadata,
  SharePlatform,
  ShareFormatResponse,
  ShareSheetState
} from "./chat/types"

export function Chat() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null)
  const [useHybrid, setUseHybrid] = useState(false)
  const [chatHistory, setChatHistory] = useState<ChatSession[]>([])
  const [showHistory, setShowHistory] = useState(false)
  const [showSources, setShowSources] = useState(false)
  const [isResearchMode, setIsResearchMode] = useState(false)
  const [researchResults, setResearchResults] = useState<Record<string, unknown>>({})
  const [shareSheet, setShareSheet] = useState<ShareSheetState | null>(null)
  const [shareCache, setShareCache] = useState<
    Record<string, Partial<Record<SharePlatform, ShareFormatResponse>>>
  >({})
  const [autocompleteSuggestions, setAutocompleteSuggestions] = useState<string[]>([])
  const [showAutocomplete, setShowAutocomplete] = useState(false)
  const [selectedFiles, setSelectedFiles] = useState<File[]>([])
  const [uploadingFiles, setUploadingFiles] = useState(false)
  const [editingMessageId, setEditingMessageId] = useState<string | null>(null)
  const [editingContent, setEditingContent] = useState("")
  const [regeneratingMessageId, setRegeneratingMessageId] = useState<string | null>(null)
  const [isCreatingSession, setIsCreatingSession] = useState(false)
  const autocompleteTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const messagesContainerRef = useRef<HTMLDivElement | null>(null)
  const messagesEndRef = useRef<HTMLDivElement | null>(null)

  const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
  const ENABLE_AUTOCOMPLETE = process.env.NEXT_PUBLIC_ENABLE_AUTOCOMPLETE !== "false"

  // Helper function to get auth headers
  const getAuthHeaders = useCallback((): Record<string, string> => {
    const token = localStorage.getItem("session_token")
    return token ? { "X-Session-Token": token } : {}
  }, [])

  const scrollMessagesToBottom = useCallback(
    (behavior: ScrollBehavior = "smooth") => {
      requestAnimationFrame(() => {
        if (messagesContainerRef.current) {
          messagesContainerRef.current.scrollTo({
            top: messagesContainerRef.current.scrollHeight,
            behavior
          })
        }
        messagesEndRef.current?.scrollIntoView({ behavior, block: "end" })
      })
    },
    []
  )

  useEffect(() => {
    scrollMessagesToBottom(messages.length < 3 ? "instant" : "smooth")
  }, [messages, isLoading, scrollMessagesToBottom])

  const findPreviousUserPrompt = useCallback(
    (messageId: string) => {
      const index = messages.findIndex((msg) => msg.id === messageId)
      if (index === -1) return undefined
      for (let i = index - 1; i >= 0; i--) {
        if (messages[i].role === "user") {
          return messages[i].content
        }
      }
      return undefined
    },
    [messages]
  )

  const loadChatHistory = useCallback(async () => {
    try {
      const headers: Record<string, string> = {
        "Content-Type": "application/json",
        ...getAuthHeaders()
      }
      const response = await fetch(`${API_BASE_URL}/chat/sessions`, {
        headers
      })
      if (response.ok) {
        const sessions = await response.json()
        setChatHistory(sessions)
      }
    } catch (error) {
      console.error("Failed to load chat history:", error)
    }
  }, [API_BASE_URL, getAuthHeaders])

  // Load chat history on component mount
  useEffect(() => {
    loadChatHistory()
  }, [loadChatHistory])

  // Autocomplete functionality
  const fetchAutocomplete = useCallback(async (query: string) => {
    if (!ENABLE_AUTOCOMPLETE || !query.trim() || query.length < 2) {
      setAutocompleteSuggestions([])
      setShowAutocomplete(false)
      return
    }

    try {
      const response = await fetch(
        `${API_BASE_URL}/api/autocomplete?q=${encodeURIComponent(query)}&max_results=5&location=Kenya&language=en`
      )
      if (response.ok) {
        const data = await response.json()
        const suggestions = data.suggestions?.map((s: { text: string }) => s.text) || []
        setAutocompleteSuggestions(suggestions)
        setShowAutocomplete(suggestions.length > 0)
      }
    } catch (error) {
      console.error("Failed to fetch autocomplete:", error)
      setAutocompleteSuggestions([])
      setShowAutocomplete(false)
    }
  }, [API_BASE_URL, ENABLE_AUTOCOMPLETE])

  // Debounced autocomplete
  useEffect(() => {
    if (!ENABLE_AUTOCOMPLETE) {
      setAutocompleteSuggestions([])
      setShowAutocomplete(false)
      return
    }

    if (autocompleteTimeoutRef.current) {
      clearTimeout(autocompleteTimeoutRef.current)
    }

    if (input.trim().length >= 2) {
      autocompleteTimeoutRef.current = setTimeout(() => {
        fetchAutocomplete(input)
      }, 300)
    } else {
      setAutocompleteSuggestions([])
      setShowAutocomplete(false)
    }

    return () => {
      if (autocompleteTimeoutRef.current) {
        clearTimeout(autocompleteTimeoutRef.current)
      }
    }
  }, [input, fetchAutocomplete, ENABLE_AUTOCOMPLETE])

  const createNewSession = async (firstMessage?: string) => {
    let title = "New Chat"
    if (firstMessage) {
      const content = firstMessage.trim()
      if (content.length <= 50) {
        title = content
      } else {
        title = content.substring(0, 50).split(' ').slice(0, -1).join(' ') + "..."
      }
    }

    try {
      const headers: Record<string, string> = {
        "Content-Type": "application/json",
        ...getAuthHeaders()
      }
      const response = await fetch(`${API_BASE_URL}/chat/sessions`, {
        method: "POST",
        headers,
        body: JSON.stringify({ title })
      })
      if (response.ok) {
        const session = await response.json()
        setCurrentSessionId(session.id)
        setMessages([])
        loadChatHistory()
        return session.id
      }
    } catch (error) {
      console.error("Failed to create session:", error)
    }
    return null
  }

  const loadSession = async (sessionId: string) => {
    try {
      const headers: Record<string, string> = {
        "Content-Type": "application/json",
        ...getAuthHeaders()
      }
      const response = await fetch(`${API_BASE_URL}/chat/sessions/${sessionId}/messages`, {
        headers
      })
      if (response.ok) {
        const sessionMessages = await response.json()
        setMessages(sessionMessages)
        setCurrentSessionId(sessionId)
        setShowHistory(false)
      }
    } catch (error) {
      console.error("Failed to load session:", error)
    }
  }

  const uploadFiles = async (sessionId: string, files: File[]): Promise<string[]> => {
    const attachmentIds: string[] = []
    setUploadingFiles(true)

    try {
      for (const file of files) {
        const formData = new FormData()
        formData.append("file", file)

        const headers: Record<string, string> = {
          ...getAuthHeaders()
        }
        const response = await fetch(`${API_BASE_URL}/chat/sessions/${sessionId}/attachments`, {
          method: "POST",
          headers,
          body: formData,
        })

        if (response.ok) {
          const data = await response.json()
          attachmentIds.push(data.attachment.id)
        } else {
          const error = await response.json()
          throw new Error(error.detail || "Failed to upload file")
        }
      }
    } finally {
      setUploadingFiles(false)
    }

    return attachmentIds
  }

  const sendMessage = useCallback(async (content: string) => {
    if (!content.trim() && selectedFiles.length === 0) return
    if (isLoading || isCreatingSession) return

    setIsLoading(true)
    try {
      let sessionId = currentSessionId
      if (!sessionId) {
        sessionId = await createNewSession(content.trim() || "File upload")
        if (!sessionId) {
          setIsLoading(false)
          return
        }
      }

      // Upload files first if any
      let attachmentIds: string[] = []
      let attachmentMetadata: Message["attachments"] = []
      if (selectedFiles.length > 0) {
        try {
          attachmentIds = await uploadFiles(sessionId, selectedFiles)
          // Fetch attachment details to display immediately
          try {
            const headers: Record<string, string> = {
              "Content-Type": "application/json",
              ...getAuthHeaders()
            }
            const attachmentPromises = attachmentIds.map(id =>
              fetch(`${API_BASE_URL}/chat/sessions/${sessionId}/attachments/${id}`, {
                headers
              })
                .then(res => res.ok ? res.json() : null)
                .catch(() => null)
            )
            const attachmentResults = await Promise.all(attachmentPromises)
            attachmentMetadata = attachmentResults
              .filter(att => att !== null)
              .map(att => ({
                id: att.id,
                filename: att.filename,
                file_type: att.file_type,
                file_size: att.file_size,
                uploaded_at: att.uploaded_at,
                processed: att.processed || false,
                cloudinary_url: att.cloudinary_url
              }))
          } catch (error) {
            console.error("Failed to fetch attachment metadata:", error)
          }
          setSelectedFiles([]) // Clear selected files after upload
        } catch (error) {
          toast.error(error instanceof Error ? error.message : "Failed to upload files")
          setIsLoading(false)
          return
        }
      }

      const userMessage: Message = {
        id: Date.now().toString(),
        session_id: sessionId,
        role: "user",
        content: content.trim() || `Uploaded ${selectedFiles.length} file(s)`,
        created_at: new Date().toISOString(),
        saved: false,
        attachments: attachmentMetadata.length > 0 ? attachmentMetadata : undefined
      }

      setMessages(prev => [...prev, userMessage])
      setInput("")
      setIsLoading(true)

      try {
        let response;
        if (isResearchMode) {
          const headers: Record<string, string> = {
            "Content-Type": "application/x-www-form-urlencoded",
            ...getAuthHeaders()
          }
          response = await fetch(`${API_BASE_URL}/research/analyze-legal-query`, {
            method: "POST",
            headers,
            body: new URLSearchParams({
              query: content.trim()
            })
          })
        } else if (useHybrid) {
          const headers: Record<string, string> = {
            "Content-Type": "application/json",
            ...getAuthHeaders()
          }
          response = await fetch(`${API_BASE_URL}/stream/query`, {
            method: "POST",
            headers,
            body: JSON.stringify({
              query: content.trim(),
              top_k: 5,
              include_sources: true,
              stream: true
            })
          })
        } else {
          const headers: Record<string, string> = {
            "Content-Type": "application/json",
            ...getAuthHeaders()
          }
          response = await fetch(`${API_BASE_URL}/chat/sessions/${sessionId}/messages`, {
            method: "POST",
            headers,
            body: JSON.stringify({
              content: content.trim(),
              role: "user",
              stream: true,
              attachment_ids: attachmentIds.length > 0 ? attachmentIds : undefined
            })
          })
        }

        if (response.ok) {
          if (isResearchMode) {
            const data = await response.json()
            const analysis = data.analysis || {}
            
            const queryInterpretation = analysis.query_interpretation || 'Analyzing your legal question...'
            const applicableLaws = Array.isArray(analysis.applicable_laws) 
              ? analysis.applicable_laws.join('\n- ') 
              : (analysis.applicable_laws || 'Researching relevant Kenyan laws...')
            const legalAnalysis = analysis.legal_analysis || 'Conducting detailed legal analysis...'
            const practicalGuidance = analysis.practical_guidance || {}
            const guidanceSteps = Array.isArray(practicalGuidance.steps) 
              ? practicalGuidance.steps 
              : (typeof practicalGuidance === 'string' ? [practicalGuidance] : ['Review the analysis above'])
            const guidanceSummary = practicalGuidance.summary || ''
            const additionalConsiderations = Array.isArray(analysis.additional_considerations)
              ? analysis.additional_considerations
              : (typeof analysis.additional_considerations === 'string' 
                ? [analysis.additional_considerations] 
                : ['Review all applicable laws'])
            const researchProcess = analysis.research_process || {}
            
            const researchContent = `
## 📋 Legal Research Analysis

**Your Question:** ${data.original_query || content.trim()}

---

### 🔍 Query Understanding

${queryInterpretation}

---

### 📖 Applicable Laws & Provisions

${Array.isArray(analysis.applicable_laws) 
  ? analysis.applicable_laws.map((law: string, idx: number) => `${idx + 1}. ${law}`).join('\n')
  : `- ${applicableLaws}`}

---

### ⚖️ Legal Analysis

${legalAnalysis}

---

### 🛠️ Practical Guidance

${guidanceSummary ? `**Summary:** ${guidanceSummary}\n\n` : ''}**Action Steps:**

${guidanceSteps.map((step: string, idx: number) => `${idx + 1}. ${step}`).join('\n')}

---

### ⚠️ Important Considerations

${additionalConsiderations.map((consideration: string) => `- ${consideration}`).join('\n')}

---

${researchProcess.steps_completed || researchProcess.sources_consulted ? `### 📊 Research Process

- **Steps Completed:** ${researchProcess.steps_completed || 0}
- **Actions Taken:** ${researchProcess.actions_taken || 0}
- **Sources Consulted:** ${researchProcess.sources_consulted || 0}
${researchProcess.tools_used && researchProcess.tools_used.length > 0 
  ? `- **Tools Used:** ${researchProcess.tools_used.join(', ')}` 
  : ''}

---\n` : ''}### 📝 Disclaimer

*This analysis is for informational purposes only and does not constitute legal advice. Please consult with a qualified legal professional for advice specific to your situation.*
            `.trim()
            
            const assistantMessage: Message = {
              id: Date.now().toString(),
              session_id: sessionId,
              role: "assistant",
              content: researchContent,
              created_at: new Date().toISOString(),
              model_used: data.model_used || "gemini-research",
              saved: true
            }
            setMessages(prev => [...prev, assistantMessage])
            
            setResearchResults(prev => ({
              ...prev,
              [assistantMessage.id]: data
            }))
          } else {
            const assistantMessageId = Date.now().toString()
            const assistantMessage: Message = {
              id: assistantMessageId,
              session_id: sessionId,
              role: "assistant",
              content: "",
              created_at: new Date().toISOString(),
              model_used: "streaming",
              saved: false
            }
            
            setMessages(prev => [...prev, assistantMessage])
            
            const reader = response.body?.getReader()
            const decoder = new TextDecoder()
            let accumulatedContent = ""
            const metadata: StreamMetadata = {}
            
            if (reader) {
              try {
                while (true) {
                  const { done, value } = await reader.read()
                  if (done) break
                  
                  const chunk = decoder.decode(value, { stream: true })
                  const lines = chunk.split('\n')
                  
                  for (const line of lines) {
                    if (line.startsWith('data: ')) {
                      const data = line.slice(6)
                      if (data === '[DONE]') continue
                      
                      if (data.startsWith('[DONE]')) {
                        try {
                          const parsed = JSON.parse(data.slice(7))
                          metadata.sources = parsed.sources || []
                          metadata.token_count = parsed.retrieved_chunks
                          metadata.model_used = parsed.model_used || (parsed.hybrid_used ? 'hybrid' : 'standard')
                          setMessages(prev => prev.map(msg => 
                            msg.id === assistantMessageId 
                              ? { 
                                  ...msg, 
                                  content: accumulatedContent,
                                  token_count: metadata.token_count,
                                  model_used: metadata.model_used,
                                  sources: metadata.sources,
                                  saved: true
                                }
                              : msg
                          ))
                          break
                        } catch {
                          // Fall through
                        }
                      }
                      
                      if (useHybrid && !data.startsWith('{') && !data.startsWith('[')) {
                        accumulatedContent += data
                        setMessages(prev => prev.map(msg => 
                          msg.id === assistantMessageId 
                            ? { ...msg, content: accumulatedContent }
                            : msg
                        ))
                        continue
                      }
                      
                      try {
                        const parsed = JSON.parse(data)
                        
                        if (parsed.type === 'sources') {
                          metadata.sources = parsed.sources
                          metadata.token_count = parsed.retrieved_chunks
                          metadata.model_used = parsed.model_used
                        } else if (parsed.type === 'content') {
                          accumulatedContent += parsed.content
                          setMessages(prev => prev.map(msg => 
                            msg.id === assistantMessageId 
                              ? { ...msg, content: accumulatedContent }
                              : msg
                          ))
                        } else if (parsed.type === 'done') {
                          setMessages(prev => prev.map(msg => 
                            msg.id === assistantMessageId 
                              ? { 
                                  ...msg, 
                                  content: parsed.full_answer || accumulatedContent,
                                  token_count: metadata.token_count,
                                  model_used: metadata.model_used,
                                  sources: metadata.sources,
                                  saved: true
                                }
                              : msg
                          ))
                          break
                        } else if (parsed.type === 'error') {
                          console.error('Streaming error:', parsed.error)
                          
                          setMessages(prev => prev.map(msg => 
                            msg.id === userMessage.id 
                              ? { ...msg, failed: true, originalQuery: content.trim() }
                              : msg
                          ))
                          
                          setMessages(prev => prev.map(msg => 
                            msg.id === assistantMessageId 
                              ? { 
                                  ...msg, 
                                  content: `Error: ${parsed.error}`,
                                  model_used: 'error',
                                  saved: true,
                                  failed: true,
                                  originalQuery: content.trim()
                                }
                              : msg
                          ))
                          break
                        }
                      } catch {
                        continue
                      }
                    }
                  }
                }
              } finally {
                reader.releaseLock()
              }
            }
          }
          loadChatHistory()
        } else {
          setMessages(prev => prev.map(msg => 
            msg.id === userMessage.id 
              ? { ...msg, failed: true, originalQuery: content.trim() }
              : msg
          ))
          
          const errorMessage: Message = {
            id: (Date.now() + 1).toString(),
            session_id: sessionId,
            role: "assistant",
            content: isResearchMode 
              ? "Sorry, I encountered an error processing your legal research request."
              : "Sorry, I encountered an error processing your request.",
            created_at: new Date().toISOString(),
            failed: true,
            originalQuery: content.trim()
          }
          setMessages(prev => [...prev, errorMessage])
        }
      } catch (error) {
        console.error("Failed to send message:", error)
        
        setMessages(prev => prev.map(msg => 
          msg.id === userMessage.id 
            ? { ...msg, failed: true, originalQuery: content.trim() }
            : msg
        ))
        
        const errorMessage: Message = {
          id: (Date.now() + 1).toString(),
          session_id: sessionId,
          role: "assistant",
          content: isResearchMode 
            ? "Sorry, I couldn't connect to the research service. Please try again."
            : "Sorry, I couldn't connect to the server. Please try again.",
          created_at: new Date().toISOString(),
          failed: true,
          originalQuery: content.trim()
        }
        setMessages(prev => [...prev, errorMessage])
      } finally {
        setIsLoading(false)
      }
    } catch (error) {
      console.error("Failed to process message:", error)
      setIsLoading(false)
    }
  }, [currentSessionId, selectedFiles, isResearchMode, useHybrid, getAuthHeaders, API_BASE_URL, loadChatHistory, createNewSession, uploadFiles])

  const submitFeedback = async (messageId: string, feedbackType: "like" | "dislike") => {
    try {
      const headers: Record<string, string> = {
        "Content-Type": "application/json",
        ...getAuthHeaders()
      }
      const response = await fetch(`${API_BASE_URL}/chat/feedback`, {
        method: "POST",
        headers,
        body: JSON.stringify({
          message_id: messageId,
          feedback_type: feedbackType
        })
      })
      
      if (response.ok) {
        setMessages(prev => prev.map(msg => 
          msg.id === messageId ? { ...msg, feedback_type: feedbackType } : msg
        ))
      }
    } catch (error) {
      console.error("Failed to submit feedback:", error)
    }
  }

  const copyToClipboard = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text)
      toast.success("Message copied to clipboard!")
    } catch (error) {
      console.error("Failed to copy to clipboard:", error)
      toast.error("Failed to copy to clipboard")
    }
  }

  const copyFailedQuery = async (message: Message) => {
    const query = message.originalQuery || message.content
    try {
      await navigator.clipboard.writeText(query)
      toast.success("Query copied to clipboard!")
    } catch (error) {
      console.error("Failed to copy query:", error)
      toast.error("Failed to copy query")
    }
  }

  const editFailedQuery = (message: Message) => {
    const query = message.originalQuery || message.content
    setInput(query)
    setTimeout(() => {
      const inputElement = document.querySelector('textarea') as HTMLTextAreaElement
      inputElement?.focus()
    }, 100)
  }

  const resendFailedQuery = async (message: Message) => {
    const query = message.originalQuery || (message.role === "user" ? message.content : "")
    if (!query.trim()) return
    
    setMessages(prev => prev.filter(msg => 
      msg.id !== message.id && 
      !(msg.failed && (msg.originalQuery === query || (msg.role === "user" && msg.content === query)))
    ))
    
    await sendMessage(query)
  }

  const startEditingMessage = (message: Message) => {
    if (message.role !== "user") return
    setEditingMessageId(message.id)
    setEditingContent(message.content)
  }

  const cancelEditing = () => {
    setEditingMessageId(null)
    setEditingContent("")
  }

  const saveEditedMessage = async (messageId: string) => {
    if (!editingContent.trim()) return
    
    const messageIndex = messages.findIndex(m => m.id === messageId)
    if (messageIndex === -1) return

    setMessages(prev => prev.slice(0, messageIndex))
    
    setEditingMessageId(null)
    setEditingContent("")
    await sendMessage(editingContent)
  }

  const regenerateMessage = async (messageId: string) => {
    const messageIndex = messages.findIndex(m => m.id === messageId)
    if (messageIndex === -1 || messages[messageIndex].role !== "assistant") return

    let userMessageIndex = -1
    let userMessageContent = ""
    for (let i = messageIndex - 1; i >= 0; i--) {
      if (messages[i].role === "user") {
        userMessageIndex = i
        userMessageContent = messages[i].content
        break
      }
    }

    if (userMessageIndex === -1) return

    setMessages(prev => prev.slice(0, userMessageIndex + 1))
    
    setRegeneratingMessageId(messageId)
    await sendMessage(userMessageContent)
    setRegeneratingMessageId(null)
  }

  const deleteSession = async (sessionId: string) => {
    if (!confirm("Are you sure you want to delete this chat session? This action cannot be undone.")) {
      return
    }

    try {
      const headers: Record<string, string> = {
        "Content-Type": "application/json",
        ...getAuthHeaders()
      }
      const response = await fetch(`${API_BASE_URL}/chat/sessions/${sessionId}`, {
        method: "DELETE",
        headers
      })
      
      if (response.ok) {
        setChatHistory(prev => prev.filter(session => session.id !== sessionId))
        if (currentSessionId === sessionId) {
          setCurrentSessionId(null)
          setMessages([])
        }
      }
    } catch (error) {
      console.error("Failed to delete session:", error)
    }
  }

  const shareChat = async (options: { silent?: boolean } = {}) => {
    if (!currentSessionId) return null

    try {
      const headers: Record<string, string> = {
        "Content-Type": "application/json",
        ...getAuthHeaders()
      }
      const response = await fetch(
        `${API_BASE_URL}/chat/share?session_id=${encodeURIComponent(currentSessionId)}`,
        {
          method: "POST",
          headers
        }
      )
      if (response.ok) {
        const data = await response.json()
        const shareUrl = `${window.location.origin}${data.share_link}`
        if (!options.silent) {
          await navigator.clipboard.writeText(shareUrl)
          toast.success("Share link copied to clipboard!")
        }
        return shareUrl
      } else {
        if (!options.silent) {
          toast.error("Failed to generate share link")
        }
      }
    } catch (error) {
      console.error("Failed to generate share link:", error)
      if (!options.silent) {
        toast.error("Failed to generate share link")
      }
    }
    return null
  }

  const generatePDF = async (messageId: string) => {
    const researchData = researchResults[messageId]
    if (!researchData) {
      toast.error("Research data not found")
      return
    }

    try {
      const response = await fetch(`${API_BASE_URL}/research/generate-pdf-report`, {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: new URLSearchParams({
          analysis_results: JSON.stringify(researchData),
          report_title: "Legal Research Report"
        })
      })

      if (response.ok) {
        const blob = await response.blob()
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = 'legal_research_report.pdf'
        document.body.appendChild(a)
        a.click()
        window.URL.revokeObjectURL(url)
        document.body.removeChild(a)
        toast.success("PDF report downloaded!")
      } else {
        toast.error("Failed to generate PDF report")
      }
    } catch (error) {
      console.error("Error generating PDF:", error)
      toast.error("Error generating PDF report")
    }
  }

  const generateWord = async (messageId: string) => {
    const researchData = researchResults[messageId]
    if (!researchData) {
      toast.error("Research data not found")
      return
    }

    try {
      const response = await fetch(`${API_BASE_URL}/research/generate-word-report`, {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: new URLSearchParams({
          analysis_results: JSON.stringify(researchData),
          report_title: "Legal Research Report"
        })
      })

      if (response.ok) {
        const blob = await response.blob()
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = 'legal_research_report.docx'
        document.body.appendChild(a)
        a.click()
        window.URL.revokeObjectURL(url)
        document.body.removeChild(a)
        toast.success("Word document downloaded!")
      } else {
        toast.error("Failed to generate Word document")
      }
    } catch (error) {
      console.error("Error generating Word document:", error)
      toast.error("Error generating Word document")
    }
  }

  const sanitizeForSharing = (content: string) => {
    if (!content) return ""
    return content.replace(/<[^>]+>/g, "").trim()
  }

  const ensureSharePreview = async (message: Message, platform: SharePlatform) => {
    const cached = shareCache[message.id]?.[platform]
    if (cached) return cached

    try {
      setShareSheet((prev) =>
        prev?.messageId === message.id
          ? { ...prev, isLoading: true, shareError: null, success: null, shareLink: null }
          : prev
      )

      const response = await fetch(`${API_BASE_URL}/share/format`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          answer: sanitizeForSharing(message.content),
          sources: message.sources || [],
          platform,
          query: findPreviousUserPrompt(message.id),
          include_hashtags: true
        })
      })

      if (!response.ok) {
        const detail = await response.text()
        throw new Error(detail || "Unable to format response")
      }

      const data: ShareFormatResponse = await response.json()
      setShareCache((prev) => ({
        ...prev,
        [message.id]: { ...(prev[message.id] || {}), [platform]: data }
      }))
      setShareSheet((prev) =>
        prev?.messageId === message.id ? { ...prev, preview: data, isLoading: false } : prev
      )
      return data
    } catch (error) {
      console.error("Failed to format post:", error)
      setShareSheet((prev) =>
        prev?.messageId === message.id
          ? {
              ...prev,
              isLoading: false,
              shareError:
                error instanceof Error ? error.message : "Unable to format this response right now."
            }
          : prev
      )
      return null
    }
  }

  const openShareSheet = (message: Message, platform: SharePlatform = "twitter") => {
    if (message.role !== "assistant") return

    if (shareSheet?.messageId === message.id && shareSheet.platform === platform) {
      setShareSheet(null)
      return
    }

    const cached = shareCache[message.id]?.[platform]
    setShareSheet({
      messageId: message.id,
      platform,
      preview: cached,
      isLoading: !cached,
      shareLink: null,
      shareError: null,
      success: null
    })

    if (!cached) {
      ensureSharePreview(message, platform)
    }
  }

  const changeSharePlatform = (message: Message, platform: SharePlatform) => {
    if (!shareSheet || shareSheet.messageId !== message.id) {
      openShareSheet(message, platform)
      return
    }

    const cached = shareCache[message.id]?.[platform]
    setShareSheet({
      ...shareSheet,
      platform,
      preview: cached,
      isLoading: !cached,
      shareLink: null,
      shareError: null,
      success: null
    })

    if (!cached) {
      ensureSharePreview(message, platform)
    }
  }

  const copyShareContent = async () => {
    if (!shareSheet?.preview) return
    const preview = shareSheet.preview
    const text = Array.isArray(preview.content) ? preview.content.join("\n\n") : preview.content

    try {
      await navigator.clipboard.writeText(text)
      toast.success("Formatted answer copied!")
    } catch (error) {
      console.error("Failed to copy share content:", error)
      toast.error("Unable to copy content")
    }
  }

  const openShareIntent = async (message: Message) => {
    if (!shareSheet) return
    const preview = shareSheet.preview ?? (await ensureSharePreview(message, shareSheet.platform))
    if (!preview) return

    try {
      setShareSheet((prev) =>
        prev ? { ...prev, shareLinkLoading: true, shareError: null, success: null } : prev
      )
      const sessionLink = await shareChat({ silent: true })

      const response = await fetch(`${API_BASE_URL}/share/generate-link`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          platform: shareSheet.platform,
          content: preview.content,
          url: sessionLink || undefined
        })
      })

      if (!response.ok) {
        const detail = await response.text()
        throw new Error(detail || "Unable to open share dialog")
      }

      const data = await response.json()
      setShareSheet((prev) =>
        prev
          ? {
              ...prev,
              shareLink: data.share_url,
              shareLinkLoading: false,
              success: `Share dialog ready for ${shareSheet.platform}`
            }
          : prev
      )
      window.open(data.share_url, "_blank", "noopener,noreferrer")
    } catch (error) {
      console.error("Failed to open share link:", error)
      setShareSheet((prev) =>
        prev
          ? {
              ...prev,
              shareLinkLoading: false,
              shareError:
                error instanceof Error
                  ? error.message
                  : "Unable to open the platform share dialog."
            }
          : prev
      )
    }
  }

  const postDirectly = async (message: Message) => {
    if (!shareSheet) return
    const preview = shareSheet.preview ?? (await ensureSharePreview(message, shareSheet.platform))
    if (!preview) return

    try {
      setShareSheet((prev) =>
        prev ? { ...prev, posting: true, shareError: null, success: null } : prev
      )

      const response = await fetch(`${API_BASE_URL}/share/post`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          platform: shareSheet.platform,
          content: preview.content,
          message_id: message.id
        })
      })

      const data = await response.json()
      if (!response.ok) {
        throw new Error(data.detail || data.message || "Unable to post to platform")
      }

      setShareSheet((prev) =>
        prev
          ? {
              ...prev,
              posting: false,
              success: data.message || "Post created successfully!",
              shareError: null
            }
          : prev
      )
      toast.success(`Posted to ${shareSheet.platform} successfully`)
    } catch (error) {
      console.error("Failed to post to platform:", error)
      setShareSheet((prev) =>
        prev
          ? {
              ...prev,
              posting: false,
              shareError:
                error instanceof Error
                  ? error.message
                  : "Unable to post automatically. Try the share dialog instead."
            }
          : prev
      )
    }
  }

  return (
    <div className="relative flex h-screen bg-gradient-to-b from-background via-background/95 to-background text-foreground overflow-hidden">
      <div className="pointer-events-none absolute inset-0 opacity-60">
        <div className="absolute -top-32 left-1/2 h-96 w-96 -translate-x-1/2 rounded-full bg-primary/20 blur-[120px]" />
        <div className="absolute bottom-0 right-0 h-80 w-80 rounded-full bg-blue-500/10 blur-[120px]" />
      </div>

      <ChatSidebar
        chatHistory={chatHistory}
        currentSessionId={currentSessionId}
        showHistory={showHistory}
        onLoadSession={loadSession}
        onDeleteSession={deleteSession}
        onCreateSession={() => createNewSession()}
        onCloseHistory={() => setShowHistory(false)}
      />

      <div className="flex-1 flex flex-col relative z-10 h-full overflow-hidden">
        <ChatHeader
          isResearchMode={isResearchMode}
          useHybrid={useHybrid}
          currentSessionId={currentSessionId}
          showHistory={showHistory}
          isLoading={isLoading}
          onToggleHistory={() => setShowHistory(!showHistory)}
          onToggleResearch={() => {
            setIsResearchMode(!isResearchMode)
            setUseHybrid(false)
          }}
          onToggleHybrid={() => {
            setUseHybrid(!useHybrid)
            setIsResearchMode(false)
          }}
          onShare={() => shareChat()}
        />

        <MessageList
          messages={messages}
          isLoading={isLoading}
          isResearchMode={isResearchMode}
          useHybrid={useHybrid}
          onSendMessage={sendMessage}
          onRegenerate={regenerateMessage}
          onFeedback={submitFeedback}
          onCopy={copyToClipboard}
          onShare={openShareSheet}
          onGeneratePDF={generatePDF}
          onGenerateWord={generateWord}
          showSources={showSources}
          onToggleSources={() => setShowSources(!showSources)}
          messagesContainerRef={messagesContainerRef}
          messagesEndRef={messagesEndRef}
          editingMessageId={editingMessageId}
          editingContent={editingContent}
          setEditingContent={setEditingContent}
          onSaveEdit={saveEditedMessage}
          onCancelEdit={cancelEditing}
          onStartEdit={startEditingMessage}
          regeneratingMessageId={regeneratingMessageId}
          shareSheet={shareSheet}
          onCloseShareSheet={() => setShareSheet(null)}
          onChangeSharePlatform={changeSharePlatform}
          onCopyShareContent={copyShareContent}
          onOpenShareIntent={openShareIntent}
          onPostDirectly={postDirectly}
          onCopyFailedQuery={copyFailedQuery}
          onEditFailedQuery={editFailedQuery}
          onResendFailedQuery={resendFailedQuery}
        />

        <ChatInput
          input={input}
          setInput={setInput}
          isLoading={isLoading}
          isResearchMode={isResearchMode}
          useHybrid={useHybrid}
          selectedFiles={selectedFiles}
          setSelectedFiles={setSelectedFiles}
          onSendMessage={sendMessage}
          enableAutocomplete={ENABLE_AUTOCOMPLETE}
          autocompleteSuggestions={autocompleteSuggestions}
          showAutocomplete={showAutocomplete}
          setShowAutocomplete={setShowAutocomplete}
        />
      </div>
    </div>
  )
}
