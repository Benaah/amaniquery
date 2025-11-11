"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Textarea } from "@/components/ui/textarea"
import { 
  Send, Bot, User, Settings, ThumbsUp, ThumbsDown, 
  Copy, Share2, History, MessageSquare, Plus
} from "lucide-react"
import Link from "next/link"

interface Message {
  id: string
  session_id: string
  role: "user" | "assistant"
  content: string
  created_at: string
  token_count?: number
  model_used?: string
  sources?: Array<{
    title: string
    url: string
    source_name: string
    category: string
    excerpt: string
  }>
  feedback_type?: "like" | "dislike"
}

interface Source {
  title: string
  url: string
  source_name: string
  category: string
  excerpt: string
}

export function Chat() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null)
  const [chatHistory, setChatHistory] = useState<ChatSession[]>([])
  const [showHistory, setShowHistory] = useState(false)
  const [copiedMessageId, setCopiedMessageId] = useState<string | null>(null)

  // Load chat history on component mount
  useEffect(() => {
    loadChatHistory()
  }, [])

  const loadChatHistory = async () => {
    try {
      const response = await fetch("http://localhost:8000/chat/sessions")
      if (response.ok) {
        const sessions = await response.json()
        setChatHistory(sessions)
      }
    } catch (error) {
      console.error("Failed to load chat history:", error)
    }
  }

  const createNewSession = async () => {
    try {
      const response = await fetch("http://localhost:8000/chat/sessions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title: "New Chat" })
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
      const response = await fetch(`http://localhost:8000/chat/sessions/${sessionId}/messages`)
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

  const sendMessage = async (content: string) => {
    if (!content.trim()) return

    let sessionId = currentSessionId
    if (!sessionId) {
      sessionId = await createNewSession()
      if (!sessionId) return
    }

    const userMessage: Message = {
      id: Date.now().toString(),
      session_id: sessionId,
      role: "user",
      content: content.trim(),
      created_at: new Date().toISOString()
    }

    setMessages(prev => [...prev, userMessage])
    setInput("")
    setIsLoading(true)

    try {
      const response = await fetch("http://localhost:8000/chat/message", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: sessionId,
          message: content.trim()
        })
      })

      if (response.ok) {
        const data = await response.json()
        const assistantMessage: Message = {
          id: (Date.now() + 1).toString(),
          session_id: sessionId,
          role: "assistant",
          content: data.response,
          created_at: new Date().toISOString(),
          token_count: data.token_count,
          model_used: data.model_used,
          sources: data.sources
        }
        setMessages(prev => [...prev, assistantMessage])
        loadChatHistory() // Refresh history to update message count
      } else {
        const errorMessage: Message = {
          id: (Date.now() + 1).toString(),
          session_id: sessionId,
          role: "assistant",
          content: "Sorry, I encountered an error processing your request.",
          created_at: new Date().toISOString()
        }
        setMessages(prev => [...prev, errorMessage])
      }
    } catch (error) {
      console.error("Failed to send message:", error)
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        session_id: sessionId,
        role: "assistant",
        content: "Sorry, I couldn't connect to the server. Please try again.",
        created_at: new Date().toISOString()
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  const submitFeedback = async (messageId: string, feedbackType: "like" | "dislike") => {
    try {
      await fetch("http://localhost:8000/chat/feedback", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message_id: messageId,
          feedback_type: feedbackType
        })
      })
      // Update local message state
      setMessages(prev => prev.map(msg => 
        msg.id === messageId ? { ...msg, feedback_type: feedbackType } : msg
      ))
    } catch (error) {
      console.error("Failed to submit feedback:", error)
    }
  }

  const copyToClipboard = async (text: string, messageId: string) => {
    try {
      await navigator.clipboard.writeText(text)
      setCopiedMessageId(messageId)
      setTimeout(() => setCopiedMessageId(null), 2000)
    } catch (error) {
      console.error("Failed to copy to clipboard:", error)
    }
  }

  const shareChat = async () => {
    if (!currentSessionId) return
    
    try {
      const response = await fetch(`http://localhost:8000/chat/sessions/${currentSessionId}/share`, {
        method: "POST"
      })
      if (response.ok) {
        const data = await response.json()
        await navigator.clipboard.writeText(data.share_url)
        alert("Share link copied to clipboard!")
      }
    } catch (error) {
      console.error("Failed to generate share link:", error)
    }
  }

  const suggestedQuestions = [
    "What are the latest developments in Kenyan constitutional law?",
    "Can you explain the recent changes to the Kenyan Penal Code?",
    "What are the key provisions of the Kenyan Competition Act?",
    "How does the Kenyan judiciary handle environmental law cases?",
    "What are the requirements for starting a business in Kenya?"
  ]

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    sendMessage(input)
  }

  const formatMessageWithCitations = (content: string, sources?: Source[]) => {
    if (!sources || sources.length === 0) return content

    // Simple citation replacement - look for [1], [2], etc.
    let formattedContent = content
    sources.forEach((source, index) => {
      const citation = `[${index + 1}]`
      formattedContent = formattedContent.replace(
        new RegExp(`\\${citation}`, 'g'),
        `<sup class="text-primary font-semibold">${index + 1}</sup>`
      )
    })

    return formattedContent
  }

  return (
    <div className="flex h-screen max-w-6xl mx-auto">
      {/* Chat History Sidebar */}
      {showHistory && (
        <div className="w-80 border-r bg-muted/30 overflow-y-auto">
          <div className="p-4 border-b">
            <div className="flex items-center justify-between">
              <h3 className="font-semibold">Chat History</h3>
              <Button 
                variant="ghost" 
                size="sm" 
                onClick={() => setShowHistory(false)}
              >
                ×
              </Button>
            </div>
            <Button 
              variant="outline" 
              size="sm" 
              className="w-full mt-2"
              onClick={createNewSession}
            >
              <Plus className="w-4 h-4 mr-2" />
              New Chat
            </Button>
          </div>
          <div className="p-2 space-y-1">
            {chatHistory.map((session) => (
              <Button
                key={session.id}
                variant={currentSessionId === session.id ? "secondary" : "ghost"}
                className="w-full justify-start text-left h-auto p-3"
                onClick={() => loadSession(session.id)}
              >
                <MessageSquare className="w-4 h-4 mr-2 flex-shrink-0" />
                <div className="flex-1 min-w-0">
                  <div className="font-medium truncate">
                    {session.title || `Chat ${session.id.slice(-8)}`}
                  </div>
                  <div className="text-xs text-muted-foreground">
                    {session.message_count} messages
                  </div>
                </div>
              </Button>
            ))}
          </div>
        </div>
      )}

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b">
          <div className="flex items-center space-x-2">
            <Button 
              variant="ghost" 
              size="sm"
              onClick={() => setShowHistory(!showHistory)}
            >
              <History className="w-4 h-4" />
            </Button>
            <h1 className="text-2xl font-bold">AmaniQuery</h1>
          </div>
          <div className="flex items-center space-x-2">
            <Badge variant="secondary">RAG-Powered Legal & News Intelligence</Badge>
            {currentSessionId && (
              <Button variant="outline" size="sm" onClick={shareChat}>
                <Share2 className="w-4 h-4 mr-2" />
                Share
              </Button>
            )}
            <Link href="/">
              <Button variant="outline" size="sm">
                <Settings className="w-4 h-4 mr-2" />
                Home
              </Button>
            </Link>
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.length === 0 && (
            <div className="text-center py-12">
              <Bot className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
              <h2 className="text-xl font-semibold mb-2">Welcome to AmaniQuery</h2>
              <p className="text-muted-foreground mb-6">
                Ask questions about Kenyan law, parliament, and news. Get factual answers with verifiable sources.
              </p>
              <div className="flex flex-col gap-4 max-w-2xl mx-auto">
                {suggestedQuestions.map((question, index) => (
                  <Button
                    key={index}
                    variant="outline"
                    className="text-left justify-start h-auto p-4 whitespace-normal"
                    onClick={() => sendMessage(question)}
                  >
                    {question}
                  </Button>
                ))}
              </div>
            </div>
          )}

          {messages.map((message) => (
            <div key={message.id} className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`flex max-w-[80%] ${message.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
                <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
                  message.role === 'user' ? 'bg-primary text-primary-foreground ml-2' : 'bg-muted mr-2'
                }`}>
                  {message.role === 'user' ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
                </div>
                <div className="flex-1">
                  <Card className={`max-w-full ${message.role === 'user' ? 'bg-primary text-primary-foreground' : ''}`}>
                    <CardContent className="p-3">
                      <div
                        className="prose prose-sm max-w-none dark:prose-invert"
                        dangerouslySetInnerHTML={{
                          __html: formatMessageWithCitations(message.content, message.sources)
                        }}
                      />
                    </CardContent>
                  </Card>
                  
                  {/* Message Actions */}
                  {message.role === 'assistant' && (
                    <div className="flex items-center space-x-2 mt-2 ml-10">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => submitFeedback(message.id, 'like')}
                        className={message.feedback_type === 'like' ? 'text-green-600' : ''}
                      >
                        <ThumbsUp className="w-4 h-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => submitFeedback(message.id, 'dislike')}
                        className={message.feedback_type === 'dislike' ? 'text-red-600' : ''}
                      >
                        <ThumbsDown className="w-4 h-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => copyToClipboard(message.content, message.id)}
                      >
                        <Copy className="w-4 h-4" />
                        {copiedMessageId === message.id && <span className="ml-1 text-xs">Copied!</span>}
                      </Button>
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}

          {isLoading && (
            <div className="flex justify-start">
              <div className="flex max-w-[80%]">
                <div className="flex-shrink-0 w-8 h-8 rounded-full bg-muted flex items-center justify-center mr-2">
                  <Bot className="w-4 h-4" />
                </div>
                <Card>
                  <CardContent className="p-3">
                    <div className="flex space-x-1">
                      <div className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce"></div>
                      <div className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce"></div>
                      <div className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce"></div>
                    </div>
                  </CardContent>
                </Card>
              </div>
            </div>
          )}
        </div>

        {/* Sources */}
        {messages.length > 0 && messages[messages.length - 1].sources && messages[messages.length - 1].sources!.length > 0 && (
          <div className="border-t p-4 bg-muted/50">
            <h3 className="font-semibold mb-2">Sources</h3>
            <div className="space-y-2">
              {messages[messages.length - 1].sources!.map((source, index) => (
                <div key={index} className="flex items-start space-x-2">
                  <sup className="text-primary font-semibold">{index + 1}</sup>
                  <div className="flex-1">
                    <a
                      href={source.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-sm font-medium hover:underline"
                    >
                      {source.title}
                    </a>
                    <p className="text-xs text-muted-foreground mt-1">{source.url}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Input */}
        <div className="border-t p-4">
          <form onSubmit={handleSubmit} className="flex space-x-2">
            <Input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask about Kenyan law, parliament, or news..."
              className="flex-1"
              disabled={isLoading}
            />
            <Button type="submit" disabled={isLoading || !input.trim()}>
              <Send className="w-4 h-4" />
            </Button>
          </form>
        </div>
      </div>
    </div>
  )
}