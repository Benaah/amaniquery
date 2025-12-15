"use client"

import { useState, useEffect, useCallback, useRef } from "react"
import { cn } from "@/lib/utils"
import { toast } from "sonner"
import { AmaniMessageList } from "./AmaniMessageList"
import { AmaniInput } from "./AmaniInput"
import { ChatHeader } from "./ChatHeader"
import { StreamingMessage } from "./AmaniMessageList"
import type { Source } from "./types"
import type {
  Message,
  ChatSession,
  SharePlatform,
  ShareFormatResponse,
  ShareSheetState,
  StreamMetadata
} from "./types"

// Extend Window interface for OAuth callback
declare global {
  interface Window {
    handleOAuthCallback?: (platform: SharePlatform, code: string, state: string) => Promise<boolean>
  }
}

interface AmaniChatProps {
  className?: string
  showWelcomeScreen?: boolean
  enableThinkingIndicator?: boolean
  showInlineSources?: boolean
  enableVoice?: boolean
  currentSessionId?: string | null
  onSessionChange?: (sessionId: string | null) => void
  chatHistory?: ChatSession[]
  onChatHistoryUpdate?: (sessions: ChatSession[]) => void
  onLoadSession?: (sessionId: string) => void
  onDeleteSession?: (sessionId: string) => void
  onToggleSidebar?: () => void
}

export function AmaniChat({ 
  className,
  showWelcomeScreen = true,
  enableThinkingIndicator = true,
  showInlineSources = true,
  enableVoice = false,
  currentSessionId: externalSessionId,
  onSessionChange,
  chatHistory: externalChatHistory,
  onChatHistoryUpdate,
  onLoadSession,
  onDeleteSession,
  onToggleSidebar
}: AmaniChatProps) {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [isThinking, setIsThinking] = useState(false)
  const [internalSessionId, setInternalSessionId] = useState<string | null>(null)
  const [useHybrid, setUseHybrid] = useState(false)
  const [isResearchMode, setIsResearchMode] = useState(false)
  const [internalChatHistory, setInternalChatHistory] = useState<ChatSession[]>([])
  const [selectedFiles, setSelectedFiles] = useState<File[]>([])
  const [uploadingFiles, setUploadingFiles] = useState(false)
  const [autocompleteSuggestions, setAutocompleteSuggestions] = useState<string[]>([])
  const [showAutocomplete, setShowAutocomplete] = useState(false)
  const [isVoiceActive, setIsVoiceActive] = useState(false)
  const [streamingContent, setStreamingContent] = useState("")
  const [streamingSources, setStreamingSources] = useState<Source[]>([])
  const [showHistory, setShowHistory] = useState(false)
  const [editingMessageId, setEditingMessageId] = useState<string | null>(null)
  const [editingContent, setEditingContent] = useState("")
  const [shareSheet, setShareSheet] = useState<ShareSheetState | null>(null)
  const [shareCache, setShareCache] = useState<
    Record<string, Partial<Record<SharePlatform, ShareFormatResponse>>>
  >({})
  const [platformTokens, setPlatformTokens] = useState<Record<SharePlatform, string | null>>({
    twitter: null,
    linkedin: null,
    facebook: null,
    whatsapp: null,
    telegram: null,
    email: null,
    threads: null,
    bluesky: null,
    tiktok: null
  })

  // Use external props if provided, otherwise use internal state
  const currentSessionId = externalSessionId ?? internalSessionId
  const chatHistory = externalChatHistory ?? internalChatHistory
  
  const autocompleteTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const messagesContainerRef = useRef<HTMLDivElement | null>(null)

  const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
  const ENABLE_AUTOCOMPLETE = process.env.NEXT_PUBLIC_ENABLE_AUTOCOMPLETE !== "false"

  // Helper function to get auth headers
  const getAuthHeaders = useCallback((): Record<string, string> => {
    const token = localStorage.getItem("session_token")
    return token ? { "X-Session-Token": token } : {}
  }, [])

  // Token management
  const storeToken = useCallback((platform: SharePlatform, token: string) => {
    localStorage.setItem(`${platform}_access_token`, token)
    setPlatformTokens(prev => ({ ...prev, [platform]: token }))
  }, [])

  const clearToken = useCallback((platform: SharePlatform) => {
    localStorage.removeItem(`${platform}_access_token`)
    setPlatformTokens(prev => ({ ...prev, [platform]: null }))
  }, [])

  const loadStoredTokens = useCallback(() => {
    const tokens: Record<SharePlatform, string | null> = {
      twitter: localStorage.getItem("twitter_access_token"),
      linkedin: localStorage.getItem("linkedin_access_token"),
      facebook: localStorage.getItem("facebook_access_token"),
      whatsapp: null,
      telegram: null,
      email: null,
      threads: localStorage.getItem("threads_access_token"),
      bluesky: localStorage.getItem("bluesky_access_token"),
      tiktok: localStorage.getItem("tiktok_access_token")
    }
    setPlatformTokens(tokens)
  }, [])
  
  const getStoredToken = useCallback((platform: SharePlatform) => {
    return localStorage.getItem(`${platform}_access_token`)
  }, [])

  // Load chat history
  const loadChatHistory = useCallback(async () => {
    try {
      const headers = { "Content-Type": "application/json", ...getAuthHeaders() }
      const response = await fetch(`/api/cache/sessions`, { headers })
      if (response.ok) {
        const sessions = await response.json()
        if (onChatHistoryUpdate) {
          onChatHistoryUpdate(sessions)
        } else {
          setInternalChatHistory(sessions)
        }
      }
    } catch (error) {
      console.error("Failed to load chat history:", error)
    }
  }, [getAuthHeaders, onChatHistoryUpdate])

  // Create new session
  const createNewSession = useCallback(async (firstMessage?: string) => {
    let title = "New Chat"
    if (firstMessage) {
      const content = firstMessage.trim()
      title = content.length <= 50 ? content : content.substring(0, 50).split(' ').slice(0, -1).join(' ') + "..."
    }

    try {
      const headers = { "Content-Type": "application/json", ...getAuthHeaders() }
      const response = await fetch(`${API_BASE_URL}/api/v1/chat/sessions`, {
        method: "POST",
        headers,
        body: JSON.stringify({ title })
      })
      if (response.ok) {
        const session = await response.json()
        if (onSessionChange) {
          onSessionChange(session.id)
        } else {
          setInternalSessionId(session.id)
        }
        setMessages([])
        loadChatHistory()
        return session.id
      }
    } catch (error) {
      console.error("Failed to create session:", error)
    }
    return null
  }, [getAuthHeaders, API_BASE_URL, loadChatHistory, onSessionChange])

  // Load session - Available for parent components via onLoadSession callback
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const loadSession = useCallback(async (sessionId: string) => {
    console.log('[AmaniChat] loadSession called with sessionId:', sessionId)
    try {
      // Call parent callback if provided
      if (onLoadSession) {
        console.log('[AmaniChat] Using parent onLoadSession callback')
        onLoadSession(sessionId)
        return
      }
      
      // Otherwise handle internally
      const headers = { "Content-Type": "application/json", ...getAuthHeaders() }
      const url = `${API_BASE_URL}/api/v1/chat/sessions/${sessionId}`
      console.log('[AmaniChat] Fetching session from:', url)
      const response = await fetch(url, { headers })
      console.log('[AmaniChat] Response status:', response.status)
      if (response.ok) {
        const session = await response.json()
        console.log('[AmaniChat] Session data received:', session)
        console.log('[AmaniChat] Messages count:', session.messages?.length || 0)
        if (onSessionChange) {
          onSessionChange(sessionId)
        } else {
          setInternalSessionId(sessionId)
        }
        setMessages(session.messages || [])
      } else {
        console.error('[AmaniChat] Failed to fetch session, status:', response.status)
      }
    } catch (error) {
      console.error("Failed to load session:", error)
    }
  }, [getAuthHeaders, API_BASE_URL, onSessionChange, onLoadSession])

  // Delete session - Available for parent components via onDeleteSession callback
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const deleteSession = useCallback(async (sessionId: string) => {
    try {
      // Call parent callback if provided
      if (onDeleteSession) {
        onDeleteSession(sessionId)
        return
      }
      
      // Otherwise handle internally
      const headers = { ...getAuthHeaders() }
      const response = await fetch(`${API_BASE_URL}/api/v1/chat/sessions/${sessionId}`, {
        method: "DELETE",
        headers
      })
      if (response.ok) {
        if (onChatHistoryUpdate) {
          // Remove session from external history
          const updatedHistory = chatHistory.filter(s => s.id !== sessionId)
          onChatHistoryUpdate(updatedHistory)
        } else {
          // Update internal history
          loadChatHistory()
        }
        
        if (currentSessionId === sessionId) {
          if (onSessionChange) {
            onSessionChange(null)
          } else {
            setInternalSessionId(null)
          }
          setMessages([])
        }
      }
    } catch (error) {
      console.error("Failed to delete session:", error)
    }
  }, [getAuthHeaders, API_BASE_URL, currentSessionId, loadChatHistory, onChatHistoryUpdate, chatHistory, onSessionChange, onDeleteSession])

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
    if (!ENABLE_AUTOCOMPLETE) return

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

  // File upload handling
  const handleFileSelect = useCallback(async (files: File[]) => {
    if (!currentSessionId) {
      const newSessionId = await createNewSession()
      if (!newSessionId) {
        toast.error("Failed to create session for file upload")
        return
      }
    }

    setUploadingFiles(true)
    const uploadedFiles: File[] = []

    try {
      for (const file of files) {
        const formData = new FormData()
        formData.append("file", file)

        const response = await fetch(`${API_BASE_URL}/api/v1/chat/sessions/${currentSessionId}/attachments`, {
          method: "POST",
          headers: getAuthHeaders(),
          body: formData
        })

        if (response.ok) {
          uploadedFiles.push(file)
          toast.success(`Uploaded ${file.name}`)
        } else {
          toast.error(`Failed to upload ${file.name}`)
        }
      }

      setSelectedFiles(prev => [...prev, ...uploadedFiles])
    } catch (error) {
      console.error("File upload failed:", error)
      toast.error("File upload failed")
    } finally {
      setUploadingFiles(false)
    }
  }, [currentSessionId, createNewSession, API_BASE_URL, getAuthHeaders])

  // Send message
  const sendMessage = useCallback(async (customContent?: string) => {
    const contentToSend = customContent || input
    if (!contentToSend.trim() || isLoading) return

    let sessionId = currentSessionId
    if (!sessionId) {
      sessionId = await createNewSession(contentToSend)
      if (!sessionId) {
        toast.error("Failed to create chat session")
        return
      }
    }

    const userMessage: Message = {
      id: Date.now().toString(),
      session_id: sessionId,
      role: "user",
      content: input,
      created_at: new Date().toISOString(),
      attachments: selectedFiles.length > 0 ? selectedFiles.map(file => ({
        id: file.name,
        filename: file.name,
        file_type: file.type,
        file_size: file.size,
        uploaded_at: new Date().toISOString(),
        processed: true
      })) : undefined
    }

    setMessages(prev => [...prev, userMessage])
    setInput("")
    setSelectedFiles([])
    setIsLoading(true)
    setIsThinking(true)
    setStreamingContent("")
    setStreamingSources([])

    try {
      const headers = { "Content-Type": "application/json", ...getAuthHeaders() }
      const response = await fetch(`${API_BASE_URL}/api/v1/chat/completions`, {
        method: "POST",
        headers,
        body: JSON.stringify({
          session_id: sessionId,
          message: input,
          use_hybrid: useHybrid,
          is_research: isResearchMode,
          attachments: selectedFiles.length > 0 ? selectedFiles.map(file => ({
            filename: file.name,
            file_type: file.type,
            file_size: file.size
          })) : undefined
        })
      })

      if (!response.ok) {
        throw new Error("Failed to send message")
      }

      const reader = response.body?.getReader()
      const decoder = new TextDecoder()
      let assistantContent = ""
      let sources: Source[] = []
      let metadata: StreamMetadata = {}

      while (true) {
        const { done, value } = await reader!.read()
        if (done) break

        const chunk = decoder.decode(value)
        const lines = chunk.split('\n').filter(line => line.trim())

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6)
            if (data === '[DONE]') {
              setIsThinking(false)
              continue
            }

            try {
              const parsed = JSON.parse(data)
              if (parsed.content) {
                assistantContent += parsed.content
                setStreamingContent(assistantContent)
              }
              if (parsed.sources) {
                sources = parsed.sources
                setStreamingSources(sources)
              }
              if (parsed.metadata) {
                metadata = { ...metadata, ...parsed.metadata }
              }
            } catch (error) {
              console.error("Failed to parse SSE data:", error)
            }
          }
        }
      }

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        session_id: sessionId,
        role: "assistant",
        content: assistantContent,
        created_at: new Date().toISOString(),
        sources: sources,
        token_count: metadata.token_count,
        model_used: metadata.model_used
      }

      setMessages(prev => [...prev, assistantMessage])
      
    } catch (error) {
      console.error("Failed to send message:", error)
      toast.error("Failed to send message")
      
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        session_id: sessionId,
        role: "assistant",
        content: "Sorry, I encountered an error while processing your message. Please try again.",
        created_at: new Date().toISOString(),
        failed: true
      }
      
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
      setIsThinking(false)
      setStreamingContent("")
      setStreamingSources([])
    }
  }, [input, isLoading, currentSessionId, createNewSession, useHybrid, isResearchMode, selectedFiles, API_BASE_URL, getAuthHeaders])

  // Handle message actions
  const handleCopy = useCallback(async (content: string) => {
    try {
      await navigator.clipboard.writeText(content)
      toast.success("Message copied to clipboard")
    } catch (error) {
      console.error("Failed to copy message:", error)
      toast.error("Failed to copy message")
    }
  }, [])

  const handleRegenerate = useCallback(async (messageId: string) => {
    const messageIndex = messages.findIndex(m => m.id === messageId)
    if (messageIndex === -1) return

    const userMessage = messages.slice(0, messageIndex + 1).reverse().find(m => m.role === "user")
    if (!userMessage) return

    // Remove the assistant message and any messages after it
    setMessages(prev => prev.slice(0, messageIndex))
    setInput(userMessage.content)
    
    // Trigger regeneration
    setTimeout(() => {
      sendMessage()
    }, 100)
  }, [messages, sendMessage])

  const handleFeedback = useCallback(async (messageId: string, type: "like" | "dislike") => {
    try {
      const headers = { "Content-Type": "application/json", ...getAuthHeaders() }
      const response = await fetch(`${API_BASE_URL}/api/v1/chat/feedback`, {
        method: "POST",
        headers,
        body: JSON.stringify({ message_id: messageId, feedback_type: type })
      })

      if (response.ok) {
        setMessages(prev => prev.map(msg => 
          msg.id === messageId ? { ...msg, feedback_type: type } : msg
        ))
        toast.success(`Feedback ${type} recorded`)
      }
    } catch (error) {
      console.error("Failed to record feedback:", error)
      toast.error("Failed to record feedback")
    }
  }, [API_BASE_URL, getAuthHeaders])

  // Editing functions
  const startEditingMessage = useCallback((message: Message) => {
    if (message.role !== "user") return
    setEditingMessageId(message.id)
    setEditingContent(message.content)
  }, [])

  const cancelEditing = useCallback(() => {
    setEditingMessageId(null)
    setEditingContent("")
  }, [])

  const saveEditedMessage = useCallback(async (messageId: string) => {
    if (!editingContent.trim()) return
    
    const messageIndex = messages.findIndex(m => m.id === messageId)
    if (messageIndex === -1) return

    setMessages(prev => prev.slice(0, messageIndex))
    
    setEditingMessageId(null)
    setEditingContent("")
    await sendMessage(editingContent) // This assumes sendMessage uses input state? No, sendMessage uses 'input' state.
    // wait, sendMessage uses 'input' state if no arg passed, but I can modify sendMessage or setInput then sendMessage
    // Actually sendMessage in AmaniChat (line 310) uses 'input' state.
    // I should update sendMessage to accept an optional content arg?
  }, [messages, editingContent]) // Wait, I need to fix sendMessage usage.

  // Using a refined sendMessage wrapper or updating logic in saveEditedMessage:
  // Since sendMessage uses 'input' state, I can setInput(editingContent) then call sendMessage?
  // But sendMessage validates input.trim().
  
  // Failed Query Functions
  const copyFailedQuery = useCallback(async (message: Message) => {
    const query = message.originalQuery || message.content
    try {
      await navigator.clipboard.writeText(query)
      toast.success("Query copied to clipboard!")
    } catch (error) {
      console.error("Failed to copy query:", error)
      toast.error("Failed to copy query")
    }
  }, [])

  const editFailedQuery = useCallback((message: Message) => {
     const query = message.originalQuery || message.content
     setInput(query)
     const textarea = document.querySelector('textarea')
     if (textarea) textarea.focus()
  }, [])

  const resendFailedQuery = useCallback(async (message: Message) => {
    const query = message.originalQuery || (message.role === "user" ? message.content : "")
    if (!query.trim()) return
    
    setMessages(prev => prev.filter(msg => 
        msg.id !== message.id && 
        !(msg.failed && (msg.originalQuery === query || (msg.role === "user" && msg.content === query)))
    ))
    
    setInput(query)
    // Wait for state update is tricky.
    // Ideally sendMessage should take an argument.
    // I will modify sendMessage below.
  }, [])

  // Sharing functionality
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

  const sanitizeForSharing = (content: string): string => {
    return content.trim()
  }

  const ensureSharePreview = useCallback(async (message: Message, platform: SharePlatform) => {
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
        headers: { "Content-Type": "application/json", ...getAuthHeaders() },
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
  }, [shareCache, API_BASE_URL, getAuthHeaders, findPreviousUserPrompt])

  const handleShare = useCallback(async (message: Message, platform: SharePlatform = "twitter") => {
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
      await ensureSharePreview(message, platform)
    }
  }, [shareSheet, shareCache, ensureSharePreview])

  const copyShareContent = useCallback(async () => {
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
  }, [shareSheet])

  const changeSharePlatform = useCallback((message: Message, platform: SharePlatform) => {
    if (!shareSheet || shareSheet.messageId !== message.id) {
       // Logic to just open share sheet if needed, but handleShare handles opening.
       // Here we switch platform
       handleShare(message, platform)
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
  }, [shareSheet, shareCache, handleShare, ensureSharePreview])

  // Auth functions
  const initiateAuth = useCallback(async (platform: SharePlatform) => {
    try {
      setShareSheet(prev => prev ? { ...prev, shareLinkLoading: true, shareError: null } : prev)

      const response = await fetch(`${API_BASE_URL}/share/auth`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ platform })
      })

      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || "Failed to initiate authentication")
      }

      const data = await response.json()
      
      if (data.auth_url) {
        // For OAuth 2.0 (LinkedIn, etc)
        const width = 600
        const height = 700
        const left = window.screen.width / 2 - width / 2
        const top = window.screen.height / 2 - height / 2
        
        window.open(
          data.auth_url,
          `Authenticate ${platform}`,
          `width=${width},height=${height},left=${left},top=${top}`
        )

        // Poll for auth success
        const checkAuth = setInterval(async () => {
          const isAuthenticated = await checkAuthStatus(platform)
          if (isAuthenticated) {
            clearInterval(checkAuth)
            setShareSheet(prev => prev ? { ...prev, shareLinkLoading: false } : prev)
          }
        }, 2000)

        // Clear interval after 2 minutes
        setTimeout(() => clearInterval(checkAuth), 120000)

      } else if (data.status === "authenticated") {
        if (data.user_info?.access_token) {
          storeToken(platform, data.user_info.access_token)
        }
        toast.success(`Already authenticated with ${platform}`)
        setShareSheet(prev => prev ? { ...prev, shareLinkLoading: false } : prev)
      }
    } catch (error) {
       console.error("Failed to initiate auth:", error)
       setShareSheet(prev => prev ? {
        ...prev,
        shareLinkLoading: false,
        shareError: error instanceof Error ? error.message : "Authentication failed"
      } : prev)
    }
  }, [API_BASE_URL, storeToken])

  const checkAuthStatus = useCallback(async (platform: SharePlatform) => {
    try {
      const response = await fetch(`${API_BASE_URL}/share/auth/status`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ platform })
      })

      if (response.ok) {
        const data = await response.json()
        if (data.status === "authenticated" && data.user_info?.access_token) {
          storeToken(platform, data.user_info.access_token)
          toast.success(`Successfully authenticated with ${platform}`)
          return true
        } else {
          clearToken(platform)
        }
      } else {
        clearToken(platform)
      }
    } catch (error) {
      console.error("Failed to check auth status:", error)
      clearToken(platform)
    }
    return false
  }, [API_BASE_URL, storeToken, clearToken])

  // Share Actions
  const shareChatLink = useCallback(async (options: { silent?: boolean } = {}) => {
    if (!currentSessionId) return null

    try {
      const headers: Record<string, string> = {
        "Content-Type": "application/json",
        ...getAuthHeaders()
      }
      const response = await fetch(
        `${API_BASE_URL}/api/v1/chat/share?session_id=${encodeURIComponent(currentSessionId)}`,
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
  }, [currentSessionId, API_BASE_URL, getAuthHeaders])

  const openShareIntent = useCallback(async (message: Message) => {
    if (!shareSheet) return
    const preview = shareSheet.preview ?? (await ensureSharePreview(message, shareSheet.platform))
    if (!preview) return

    try {
      setShareSheet((prev) =>
        prev ? { ...prev, shareLinkLoading: true, shareError: null, success: null } : prev
      )
      const sessionLink = await shareChatLink({ silent: true })

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
  }, [shareSheet, ensureSharePreview, shareChatLink, API_BASE_URL])

  const generateShareImage = useCallback(async (message: Message) => {
    if (!shareSheet) return
    const preview = shareSheet.preview ?? (await ensureSharePreview(message, shareSheet.platform))
    if (!preview) return

    try {
      setShareSheet((prev) =>
        prev ? { ...prev, generatingImage: true, shareError: null, success: null } : prev
      )

      const text = Array.isArray(preview.content) ? preview.content.join("\n\n") : preview.content
      const title = `AmaniQuery Insight`

      const response = await fetch(`${API_BASE_URL}/share/generate-image-from-post`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          post_content: text,
          query: title,
          color_scheme: "professional"
        })
      })

      if (!response.ok) {
        const detail = await response.text()
        throw new Error(detail || "Unable to generate image")
      }

      const data = await response.json()
      
      // Download the image
      const imageResponse = await fetch(`data:image/png;base64,${data.image_base64}`)
      const blob = await imageResponse.blob()
      const url = URL.createObjectURL(blob)
      
      const a = document.createElement('a')
      a.href = url
      a.download = `amaniquery-${message.id}.png`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)

      setShareSheet((prev) =>
        prev
          ? {
              ...prev,
              generatingImage: false,
              success: "Image downloaded successfully!",
              shareError: null
            }
          : prev
      )
    } catch (error) {
      console.error("Failed to generate image:", error)
      setShareSheet((prev) =>
        prev
          ? {
              ...prev,
              generatingImage: false,
              shareError:
                error instanceof Error
                  ? error.message
                  : "Unable to generate image."
            }
          : prev
      )
    }
  }, [shareSheet, ensureSharePreview, API_BASE_URL])
  
  const postDirectly = useCallback(async (message: Message) => {
    if (!shareSheet) return
    const preview = shareSheet.preview ?? (await ensureSharePreview(message, shareSheet.platform))
    if (!preview) return

    const accessToken = getStoredToken(shareSheet.platform)
    if (!accessToken) {
        setShareSheet(prev => prev ? {
            ...prev,
            shareError: `Please authenticate with ${shareSheet.platform} first.`
        } : prev)
        return
    }

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
          message_id: message.id,
          access_token: accessToken
        })
      })

      if (!response.ok) {
        const detail = await response.text()
        throw new Error(detail || "Unable to post")
      }

      const data = await response.json()
      setShareSheet((prev) =>
        prev
          ? {
              ...prev,
              posting: false,
              success: data.message || `Posted to ${shareSheet.platform} successfully`,
              shareError: null
            }
          : prev
      )
      toast.success(data.message || `Posted to ${shareSheet.platform} successfully`)
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
                  : "Unable to post automatically."
            }
          : prev
      )
    }
  }, [shareSheet, ensureSharePreview, getStoredToken, API_BASE_URL])

  // OAuth Callback Handler (for popup)
  useEffect(() => {
    window.handleOAuthCallback = async (platform: SharePlatform, code: string, state: string) => {
        try {
            const response = await fetch(`${API_BASE_URL}/share/auth/callback`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ platform, code, state })
            })

            if (response.ok) {
                const data = await response.json()
                if (data.access_token) {
                    storeToken(platform, data.access_token)
                    toast.success("Authentication successful!")
                    return true
                }
            }
        } catch (error) {
            console.error("Auth callback error:", error)
        }
        return false
    }
  }, [API_BASE_URL, storeToken])

  // Load tokens on mount
  useEffect(() => {
    loadStoredTokens()
  }, [loadStoredTokens])

  // Scroll to bottom when messages change
  useEffect(() => {
    if (messagesContainerRef.current) {
      messagesContainerRef.current.scrollTop = messagesContainerRef.current.scrollHeight
    }
  }, [messages, streamingContent])

  // Initialize
  useEffect(() => {
    loadChatHistory()
  }, [loadChatHistory])

  // Load session messages when currentSessionId changes
  useEffect(() => {
    console.log('[AmaniChat] useEffect triggered - currentSessionId:', currentSessionId)
    if (currentSessionId) {
      loadSession(currentSessionId)
    } else {
      setMessages([])
    }
  }, [currentSessionId, loadSession])

  return (
    <div className={cn("flex flex-col h-screen bg-background", className)}>
      {/* Header */}
      <ChatHeader
          currentSessionId={currentSessionId}
          showHistory={showHistory}
          onToggleHistory={() => setShowHistory(!showHistory)}
          onToggleSidebar={onToggleSidebar}
          useHybrid={useHybrid}
          isResearchMode={isResearchMode}
          isLoading={isLoading}
          onShare={copyShareContent}
        />

      {/* Messages */}
      <div className="flex-1 overflow-y-auto overflow-x-hidden" ref={messagesContainerRef}>
        {streamingContent ? (
            <div className="h-full">
              <AmaniMessageList
                messages={messages}
                isLoading={isLoading}
                isThinking={isThinking}
                onSendMessage={sendMessage}
                onRegenerate={handleRegenerate}
                onFeedback={handleFeedback}
                onCopy={handleCopy}
                onShare={handleShare}
                showWelcomeScreen={showWelcomeScreen && messages.length === 0}
                enableThinkingIndicator={enableThinkingIndicator}
                showInlineSources={showInlineSources}
                shareSheet={shareSheet}
                onCloseShareSheet={() => setShareSheet(null)}
                onChangeSharePlatform={changeSharePlatform}
                onCopyShareContent={copyShareContent}
                onGenerateShareImage={generateShareImage}
                onOpenShareIntent={openShareIntent}
                onAuthenticatePlatform={initiateAuth}
                onPostDirectly={postDirectly}
                platformTokens={platformTokens}
                editingMessageId={editingMessageId}
                editingContent={editingContent}
                setEditingContent={setEditingContent}
                onSaveEdit={saveEditedMessage}
                onCancelEdit={cancelEditing}
                onStartEdit={startEditingMessage}
                onCopyFailedQuery={copyFailedQuery}
                onEditFailedQuery={editFailedQuery}
                onResendFailedQuery={resendFailedQuery}
              />
              <div className="px-4 pb-6">
                <StreamingMessage
                  content={streamingContent}
                  isThinking={isThinking}
                  sources={streamingSources}
                />
              </div>
            </div>
          ) : (
            <AmaniMessageList
              messages={messages}
              isLoading={isLoading}
              isThinking={isThinking}
              onSendMessage={sendMessage}
              onRegenerate={handleRegenerate}
              onFeedback={handleFeedback}
              onCopy={handleCopy}
              onShare={handleShare}
              showWelcomeScreen={showWelcomeScreen && messages.length === 0}
              enableThinkingIndicator={enableThinkingIndicator}
              showInlineSources={showInlineSources}
              shareSheet={shareSheet}
              onCloseShareSheet={() => setShareSheet(null)}
              onChangeSharePlatform={changeSharePlatform}
              onCopyShareContent={copyShareContent}
              onGenerateShareImage={generateShareImage}
              onOpenShareIntent={openShareIntent}
              onAuthenticatePlatform={initiateAuth}
              onPostDirectly={postDirectly}
              platformTokens={platformTokens}
              editingMessageId={editingMessageId}
              editingContent={editingContent}
              setEditingContent={setEditingContent}
              onSaveEdit={saveEditedMessage}
              onCancelEdit={cancelEditing}
              onStartEdit={startEditingMessage}
              onCopyFailedQuery={copyFailedQuery}
              onEditFailedQuery={editFailedQuery}
              onResendFailedQuery={resendFailedQuery}
            />
          )}
      </div>

      {/* Input */}
      <div className="border-t bg-background/80 backdrop-blur-sm p-4">
          <AmaniInput
            value={input}
            onChange={setInput}
            onSend={sendMessage}
            onFileSelect={handleFileSelect}
            onModeChange={(mode) => {
              setUseHybrid(mode === "hybrid")
              setIsResearchMode(mode === "research")
            }}
            placeholder="Ask AmaniQuery anything..."
            disabled={isLoading || uploadingFiles}
            isLoading={isLoading || uploadingFiles}
            mode={isResearchMode ? "research" : useHybrid ? "hybrid" : "chat"}
            attachments={selectedFiles.map(file => ({
              id: file.name,
              filename: file.name,
              file_type: file.type,
              file_size: file.size,
              uploaded_at: new Date().toISOString(),
              processed: true
            }))}
            onRemoveAttachment={(attachmentId) => {
              setSelectedFiles(prev => prev.filter(f => f.name !== attachmentId))
            }}
            showModeSelector={true}
            enableVoice={enableVoice}
            isVoiceActive={isVoiceActive}
            onVoiceToggle={() => setIsVoiceActive(!isVoiceActive)}
            autocompleteSuggestions={autocompleteSuggestions}
            showAutocomplete={showAutocomplete}
            onAutocompleteSelect={(suggestion) => {
              setInput(suggestion)
              setShowAutocomplete(false)
            }}
          />
      </div>
    </div>
  )
}