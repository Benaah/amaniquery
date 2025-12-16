import { render, screen, fireEvent, waitFor } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { AmaniChat } from "../AmaniChat"
import { AmaniMessage } from "../AmaniMessage"
import { AmaniInput } from "../AmaniInput"
import { AmaniMessageList } from "../AmaniMessageList"
import { ThinkingIndicator } from "../ThinkingIndicator"
import { MessageActions } from "../MessageActions"
import { SourcePanel } from "../SourcePanel"

// Mock the auth context and other dependencies
jest.mock("@/lib/auth-context", () => ({
  useAuth: () => ({
    isAuthenticated: true,
    loading: false
  })
}))

jest.mock("sonner", () => ({
  toast: {
    success: jest.fn(),
    error: jest.fn()
  }
}))

// Mock fetch
global.fetch = jest.fn()

const mockMessages = [
  {
    id: "1",
    session_id: "test-session",
    role: "user" as const,
    content: "What is the capital of Kenya?",
    created_at: new Date().toISOString()
  },
  {
    id: "2",
    session_id: "test-session",
    role: "assistant" as const,
    content: "The capital of Kenya is Nairobi.",
    created_at: new Date().toISOString(),
    sources: [
      {
        title: "Kenya - Wikipedia",
        url: "https://en.wikipedia.org/wiki/Kenya",
        source_name: "Wikipedia",
        category: "encyclopedia",
        excerpt: "Kenya is a country in East Africa with its capital in Nairobi."
      }
    ]
  }
]

describe("AmaniMessage Component", () => {
  it("renders user message correctly", () => {
    const userMessage = mockMessages[0]
    const { container } = render(
      <AmaniMessage
        message={userMessage}
        onCopy={jest.fn()}
        onRegenerate={jest.fn()}
        onFeedback={jest.fn()}
      />
    )

    expect(container.textContent).toContain("What is the capital of Kenya?")
    expect(container.querySelector("[data-user-avatar]")).toBeTruthy()
  })

  it("renders assistant message with citations", () => {
    const assistantMessage = mockMessages[1]
    const { container } = render(
      <AmaniMessage
        message={assistantMessage}
        onCopy={jest.fn()}
        onRegenerate={jest.fn()}
        onFeedback={jest.fn()}
      />
    )

    expect(container.textContent).toContain("The capital of Kenya is Nairobi.")
    expect(container.querySelector("[data-assistant-avatar]")).toBeTruthy()
    // Should render citation
    expect(container.textContent).toContain("[1]")
  })

  it("handles copy action", async () => {
    const mockCopy = jest.fn()
    const assistantMessage = mockMessages[1]
    
    render(
      <AmaniMessage
        message={assistantMessage}
        onCopy={mockCopy}
        onRegenerate={jest.fn()}
        onFeedback={jest.fn()}
      />
    )

    const copyButton = screen.getByRole("button", { name: /copy/i })
    await userEvent.click(copyButton)

    expect(mockCopy).toHaveBeenCalledWith("The capital of Kenya is Nairobi.")
  })

  it("shows feedback buttons on hover", async () => {
    const assistantMessage = mockMessages[1]
    const { container } = render(
      <AmaniMessage
        message={assistantMessage}
        onCopy={jest.fn()}
        onRegenerate={jest.fn()}
        onFeedback={jest.fn()}
      />
    )

    const messageElement = container.querySelector("[data-message]")
    if (messageElement) {
      fireEvent.mouseEnter(messageElement)
      
      await waitFor(() => {
        expect(screen.getByRole("button", { name: /like/i })).toBeInTheDocument()
        expect(screen.getByRole("button", { name: /dislike/i })).toBeInTheDocument()
      })
    }
  })
})

describe("ThinkingIndicator Component", () => {
  it("renders when active", () => {
    render(<ThinkingIndicator isActive={true} />)
    
    expect(screen.getByText("Thinking")).toBeInTheDocument()
    expect(screen.getByRole("button", { name: /expand/i })).toBeInTheDocument()
  })

  it("does not render when inactive", () => {
    render(<ThinkingIndicator isActive={false} />)
    
    expect(screen.queryByText("Thinking")).not.toBeInTheDocument()
  })

  it("expands and collapses", async () => {
    render(<ThinkingIndicator isActive={true} />)
    
    const expandButton = screen.getByRole("button", { name: /expand/i })
    await userEvent.click(expandButton)
    
    // Should show thinking steps when expanded
    expect(screen.getByText("Understanding your question")).toBeInTheDocument()
  })
})

describe("MessageActions Component", () => {
  const mockMessage = mockMessages[1]
  const mockHandlers = {
    onCopy: jest.fn(),
    onRegenerate: jest.fn(),
    onFeedback: jest.fn(),
    onShare: jest.fn()
  }

  it("renders all action buttons", () => {
    render(<MessageActions message={mockMessage} {...mockHandlers} />)
    
    expect(screen.getByRole("button", { name: /copy/i })).toBeInTheDocument()
    expect(screen.getByRole("button", { name: /regenerate/i })).toBeInTheDocument()
    expect(screen.getByRole("button", { name: /like/i })).toBeInTheDocument()
    expect(screen.getByRole("button", { name: /dislike/i })).toBeInTheDocument()
    expect(screen.getByRole("button", { name: /share/i })).toBeInTheDocument()
  })

  it("handles feedback correctly", async () => {
    render(<MessageActions message={mockMessage} {...mockHandlers} />)
    
    const likeButton = screen.getByRole("button", { name: /like/i })
    await userEvent.click(likeButton)
    
    expect(mockHandlers.onFeedback).toHaveBeenCalledWith("2", "like")
  })

  it("shows compact mode", () => {
    render(<MessageActions message={mockMessage} {...mockHandlers} compact={true} />)
    
    // In compact mode, should have more menu
    expect(screen.getByRole("button", { name: /more/i })).toBeInTheDocument()
  })
})

describe("SourcePanel Component", () => {
  const mockSources = [
    {
      title: "Test Source 1",
      url: "https://example1.com",
      source_name: "Example 1",
      category: "news",
      excerpt: "This is a test excerpt for source 1."
    },
    {
      title: "Test Source 2",
      url: "https://example2.com",
      source_name: "Example 2",
      category: "academic",
      excerpt: "This is a test excerpt for source 2."
    }
  ]

  it("renders panel variant", () => {
    render(
      <SourcePanel
        sources={mockSources}
        isOpen={true}
        onToggle={jest.fn()}
        variant="panel"
      />
    )
    
    expect(screen.getByText("Sources")).toBeInTheDocument()
    expect(screen.getByText("Test Source 1")).toBeInTheDocument()
    expect(screen.getByText("Test Source 2")).toBeInTheDocument()
  })

  it("renders inline variant", () => {
    render(
      <SourcePanel
        sources={mockSources}
        isOpen={true}
        onToggle={jest.fn()}
        variant="inline"
      />
    )
    
    expect(screen.getByText("Sources")).toBeInTheDocument()
    expect(screen.getByText("Example 1")).toBeInTheDocument()
  })

  it("filters by category", async () => {
    render(
      <SourcePanel
        sources={mockSources}
        isOpen={true}
        onToggle={jest.fn()}
        variant="panel"
      />
    )
    
    const newsFilter = screen.getByRole("button", { name: /news/i })
    await userEvent.click(newsFilter)
    
    // Should only show news sources
    expect(screen.getByText("Test Source 1")).toBeInTheDocument()
    expect(screen.queryByText("Test Source 2")).not.toBeInTheDocument()
  })
})

describe("AmaniInput Component", () => {
  const mockHandlers = {
    onChange: jest.fn(),
    onSend: jest.fn(),
    onFileSelect: jest.fn()
  }

  it("renders input field with placeholder", () => {
    render(<AmaniInput value="" {...mockHandlers} />)
    
    const input = screen.getByPlaceholderText("Ask anything...")
    expect(input).toBeInTheDocument()
    expect(input.tagName).toBe("TEXTAREA")
  })

  it("handles text input", async () => {
    render(<AmaniInput value="" {...mockHandlers} />)
    
    const input = screen.getByPlaceholderText("Ask anything...")
    await userEvent.type(input, "Hello AmaniQuery")
    
    expect(mockHandlers.onChange).toHaveBeenCalledWith("H")
    expect(mockHandlers.onChange).toHaveBeenCalledWith("He")
    expect(mockHandlers.onChange).toHaveBeenCalledWith("Hello AmaniQuery")
  })

  it("sends message on Enter key", async () => {
    render(<AmaniInput value="Test message" {...mockHandlers} />)
    
    const input = screen.getByPlaceholderText("Ask anything...")
    await userEvent.type(input, "{Enter}")
    
    expect(mockHandlers.onSend).toHaveBeenCalled()
  })

  it("shows mode selector", () => {
    render(<AmaniInput value="" {...mockHandlers} showModeSelector={true} />)
    
    expect(screen.getByRole("button", { name: /chat/i })).toBeInTheDocument()
  })

  it("handles file selection", async () => {
    const mockFileSelect = jest.fn()
    render(<AmaniInput value="" {...mockHandlers} onFileSelect={mockFileSelect} />)
    
    const fileInput = screen.getByLabelText("file-upload")
    const file = new File(["test content"], "test.txt", { type: "text/plain" })
    
    Object.defineProperty(fileInput, "files", {
      value: [file]
    })
    
    fireEvent.change(fileInput)
    
    expect(mockFileSelect).toHaveBeenCalledWith([file])
  })
})

describe("AmaniMessageList Component", () => {
  it("renders message list", () => {
    render(
      <AmaniMessageList
        messages={mockMessages}
        isLoading={false}
        onSendMessage={jest.fn()}
        onRegenerate={jest.fn()}
        onFeedback={jest.fn()}
        onCopy={jest.fn()}
        onShare={jest.fn()}
      />
    )
    
    expect(screen.getByText("What is the capital of Kenya?")).toBeInTheDocument()
    expect(screen.getByText("The capital of Kenya is Nairobi.")).toBeInTheDocument()
  })

  it("shows welcome screen when no messages", () => {
    render(
      <AmaniMessageList
        messages={[]}
        isLoading={false}
        onSendMessage={jest.fn()}
        onRegenerate={jest.fn()}
        onFeedback={jest.fn()}
        onCopy={jest.fn()}
        onShare={jest.fn()}
        showWelcomeScreen={true}
      />
    )
    
    expect(screen.getByText(/welcome to amaniquery/i)).toBeInTheDocument()
  })

  it("shows loading state", () => {
    render(
      <AmaniMessageList
        messages={[]}
        isLoading={true}
        onSendMessage={jest.fn()}
        onRegenerate={jest.fn()}
        onFeedback={jest.fn()}
        onCopy={jest.fn()}
        onShare={jest.fn()}
      />
    )
    
    expect(screen.getByText(/amaniquery is thinking/i)).toBeInTheDocument()
  })
})

describe("AmaniChat Integration", () => {
  beforeEach(() => {
    // Reset fetch mock
    (global.fetch as jest.Mock).mockReset()
    
    // Mock successful responses
    ;(global.fetch as jest.Mock).mockImplementation((url: string) => {
      if (url.includes('/api/cache/sessions')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve([]),
          headers: new Headers()
        })
      }
      if (url.includes('/api/v1/chat/sessions')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ id: 'test-session', title: 'Test Chat' })
        })
      }
      return Promise.resolve({ ok: true, json: () => Promise.resolve({}) })
    })
  })

  it("renders complete chat interface", () => {
    render(<AmaniChat />)
    
    // Should have input field
    expect(screen.getByPlaceholderText("Ask AmaniQuery anything...")).toBeInTheDocument()
    
    // Should have mode selector
    expect(screen.getByRole("button", { name: /chat/i })).toBeInTheDocument()
  })

  it("handles message sending flow", async () => {
    render(<AmaniChat />)
    
    const input = screen.getByPlaceholderText("Ask AmaniQuery anything...")
    await userEvent.type(input, "Hello AmaniQuery")
    
    const sendButton = screen.getByRole("button", { name: /send/i })
    await userEvent.click(sendButton)
    
    // Input should be cleared
    expect(input).toHaveValue("")
  })

  it("shows thinking indicator during response", async () => {
    // Mock streaming response
    const mockReader = {
      read: jest.fn()
        .mockResolvedValueOnce({ done: false, value: new TextEncoder().encode('data: {"content": "Hello"}\n\n') })
        .mockResolvedValueOnce({ done: true, value: new Uint8Array() })
    }
    
    ;(global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      body: { getReader: () => mockReader }
    })
    
    render(<AmaniChat />)
    
    const input = screen.getByPlaceholderText("Ask AmaniQuery anything...")
    await userEvent.type(input, "Test message")
    
    const sendButton = screen.getByRole("button", { name: /send/i })
    await userEvent.click(sendButton)
    
    // Should show loading state
    await waitFor(() => {
      expect(screen.getByText(/thinking/i)).toBeInTheDocument()
    })
  })
})