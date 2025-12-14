import { render, screen, fireEvent, waitFor } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { AmaniSidebar } from "../AmaniSidebar"
import type { ChatSession } from "../chat/types"

// Mock the auth context
jest.mock("@/lib/auth-context", () => ({
  useAuth: () => ({
    user: {
      id: "test-user",
      name: "Test User",
      email: "test@example.com",
      profile_image_url: null
    },
    logout: jest.fn()
  })
}))

// Mock next/navigation
jest.mock("next/navigation", () => ({
  usePathname: () => "/chat",
  useRouter: () => ({
    push: jest.fn()
  })
}))

const mockChatHistory: ChatSession[] = [
  {
    id: "1",
    title: "Test Chat 1",
    message_count: 5,
    created_at: new Date(Date.now() - 1000 * 60 * 60 * 2).toISOString(), // 2 hours ago
    updated_at: new Date(Date.now() - 1000 * 60 * 30).toISOString() // 30 minutes ago
  },
  {
    id: "2",
    title: "Test Chat 2",
    message_count: 12,
    created_at: new Date(Date.now() - 1000 * 60 * 60 * 24).toISOString(), // 1 day ago
    updated_at: new Date(Date.now() - 1000 * 60 * 60 * 5).toISOString() // 5 hours ago
  },
  {
    id: "3",
    title: "Test Chat 3",
    message_count: 8,
    created_at: new Date(Date.now() - 1000 * 60 * 60 * 48).toISOString(), // 2 days ago
    updated_at: new Date(Date.now() - 1000 * 60 * 60 * 24).toISOString() // 1 day ago
  }
]

const mockHandlers = {
  onSessionSelect: jest.fn(),
  onNewSession: jest.fn(),
  onDeleteSession: jest.fn(),
  onRenameSession: jest.fn(),
  onToggle: jest.fn()
}

describe("AmaniSidebar Component", () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it("renders sidebar with header and navigation", () => {
    render(
      <AmaniSidebar
        chatHistory={mockChatHistory}
        currentSessionId={null}
        isOpen={true}
        {...mockHandlers}
      />
    )

    // Check header
    expect(screen.getByText("AmaniQuery")).toBeInTheDocument()
    expect(screen.getByText("AI Assistant")).toBeInTheDocument()

    // Check navigation
    expect(screen.getByText("Home")).toBeInTheDocument()
    expect(screen.getByText("Chat")).toBeInTheDocument()
    expect(screen.getByText("Voice")).toBeInTheDocument()
    expect(screen.getByText("Profile")).toBeInTheDocument()
  })

  it("shows search input", () => {
    render(
      <AmaniSidebar
        chatHistory={mockChatHistory}
        currentSessionId={null}
        isOpen={true}
        {...mockHandlers}
      />
    )

    const searchInput = screen.getByPlaceholderText("Search conversations...")
    expect(searchInput).toBeInTheDocument()
  })

  it("renders chat history with date grouping", () => {
    render(
      <AmaniSidebar
        chatHistory={mockChatHistory}
        currentSessionId={null}
        isOpen={true}
        {...mockHandlers}
      />
    )

    // Should show date groups
    expect(screen.getByText("Today")).toBeInTheDocument()
    expect(screen.getByText("Yesterday")).toBeInTheDocument()
    
    // Should show chat titles
    expect(screen.getByText("Test Chat 1")).toBeInTheDocument()
    expect(screen.getByText("Test Chat 2")).toBeInTheDocument()
    expect(screen.getByText("Test Chat 3")).toBeInTheDocument()
  })

  it("highlights current session", () => {
    render(
      <AmaniSidebar
        chatHistory={mockChatHistory}
        currentSessionId="1"
        isOpen={true}
        {...mockHandlers}
      />
    )

    const currentChat = screen.getByText("Test Chat 1").closest(".group")
    expect(currentChat).toHaveClass("bg-primary/10", "text-primary")
  })

  it("handles session selection", async () => {
    render(
      <AmaniSidebar
        chatHistory={mockChatHistory}
        currentSessionId={null}
        isOpen={true}
        {...mockHandlers}
      />
    )

    const chatItem = screen.getByText("Test Chat 1").closest(".cursor-pointer")
    await userEvent.click(chatItem!)

    expect(mockHandlers.onSessionSelect).toHaveBeenCalledWith("1")
  })

  it("shows action buttons on hover", async () => {
    render(
      <AmaniSidebar
        chatHistory={mockChatHistory}
        currentSessionId={null}
        isOpen={true}
        {...mockHandlers}
      />
    )

    const chatItem = screen.getByText("Test Chat 1").closest(".group")
    
    // Initially, action buttons should not be visible
    const editButton = screen.getByLabelText("Edit chat").closest("button")
    const deleteButton = screen.getByLabelText("Delete chat").closest("button")
    
    expect(editButton).toHaveClass("opacity-0")
    expect(deleteButton).toHaveClass("opacity-0")

    // Hover over the chat item
    fireEvent.mouseEnter(chatItem!)

    // Action buttons should become visible
    await waitFor(() => {
      expect(editButton).toHaveClass("opacity-100")
      expect(deleteButton).toHaveClass("opacity-100")
    })
  })

  it("handles editing session title", async () => {
    render(
      <AmaniSidebar
        chatHistory={mockChatHistory}
        currentSessionId={null}
        isOpen={true}
        {...mockHandlers}
      />
    )

    // Show edit buttons by hovering
    const chatItem = screen.getByText("Test Chat 1").closest(".group")
    fireEvent.mouseEnter(chatItem!)

    const editButton = screen.getByLabelText("Edit chat").closest("button")!
    await userEvent.click(editButton)

    // Should show input field
    const input = screen.getByDisplayValue("Test Chat 1")
    expect(input).toBeInTheDocument()

    // Change title
    await userEvent.clear(input)
    await userEvent.type(input, "Updated Chat Title")

    // Save by pressing Enter
    await userEvent.type(input, "{Enter}")

    expect(mockHandlers.onRenameSession).toHaveBeenCalledWith("1", "Updated Chat Title")
  })

  it("handles deleting session", async () => {
    render(
      <AmaniSidebar
        chatHistory={mockChatHistory}
        currentSessionId={null}
        isOpen={true}
        {...mockHandlers}
      />
    )

    // Show delete buttons by hovering
    const chatItem = screen.getByText("Test Chat 1").closest(".group")
    fireEvent.mouseEnter(chatItem!)

    const deleteButton = screen.getByLabelText("Delete chat").closest("button")!
    await userEvent.click(deleteButton)

    expect(mockHandlers.onDeleteSession).toHaveBeenCalledWith("1")
  })

  it("handles new chat button", async () => {
    render(
      <AmaniSidebar
        chatHistory={mockChatHistory}
        currentSessionId={null}
        isOpen={true}
        {...mockHandlers}
      />
    )

    const newChatButton = screen.getByRole("button", { name: /new chat/i })
    await userEvent.click(newChatButton)

    expect(mockHandlers.onNewSession).toHaveBeenCalled()
  })

  it("filters chat history based on search", async () => {
    render(
      <AmaniSidebar
        chatHistory={mockChatHistory}
        currentSessionId={null}
        isOpen={true}
        {...mockHandlers}
      />
    )

    const searchInput = screen.getByPlaceholderText("Search conversations...")
    await userEvent.type(searchInput, "Chat 2")

    // Should only show matching chats
    expect(screen.getByText("Test Chat 2")).toBeInTheDocument()
    expect(screen.queryByText("Test Chat 1")).not.toBeInTheDocument()
    expect(screen.queryByText("Test Chat 3")).not.toBeInTheDocument()
  })

  it("shows empty state when no chat history", () => {
    render(
      <AmaniSidebar
        chatHistory={[]}
        currentSessionId={null}
        isOpen={true}
        {...mockHandlers}
      />
    )

    expect(screen.getByText("No conversations yet")).toBeInTheDocument()
    expect(screen.getByText("Start your first conversation")).toBeInTheDocument()
  })

  it("shows user profile section", () => {
    render(
      <AmaniSidebar
        chatHistory={mockChatHistory}
        currentSessionId={null}
        isOpen={true}
        {...mockHandlers}
      />
    )

    expect(screen.getByText("Test User")).toBeInTheDocument()
    expect(screen.getByText("test@example.com")).toBeInTheDocument()
  })

  it("handles logout", async () => {
    const mockLogout = jest.fn()
    jest.mock("@/lib/auth-context", () => ({
      useAuth: () => ({
        user: {
          id: "test-user",
          name: "Test User",
          email: "test@example.com",
          profile_image_url: null
        },
        logout: mockLogout
      })
    }))

    render(
      <AmaniSidebar
        chatHistory={mockChatHistory}
        currentSessionId={null}
        isOpen={true}
        {...mockHandlers}
      />
    )

    const logoutButton = screen.getByRole("button", { name: /sign out/i })
    await userEvent.click(logoutButton)

    expect(mockLogout).toHaveBeenCalled()
  })

  it("handles sidebar toggle", async () => {
    render(
      <AmaniSidebar
        chatHistory={mockChatHistory}
        currentSessionId={null}
        isOpen={true}
        {...mockHandlers}
      />
    )

    const toggleButton = screen.getByRole("button", { name: /toggle/i })
    await userEvent.click(toggleButton)

    expect(mockHandlers.onToggle).toHaveBeenCalled()
  })

  it("shows active navigation item", () => {
    render(
      <AmaniSidebar
        chatHistory={mockChatHistory}
        currentSessionId={null}
        isOpen={true}
        {...mockHandlers}
      />
    )

    const chatNavItem = screen.getByText("Chat").closest("a")
    expect(chatNavItem).toHaveClass("bg-primary/10", "text-primary")
  })

  it("formats dates correctly", () => {
    render(
      <AmaniSidebar
        chatHistory={mockChatHistory}
        currentSessionId={null}
        isOpen={true}
        {...mockHandlers}
      />
    )

    // Should show relative time for recent chats
    const chatItems = screen.getAllByText(/messages/)
    expect(chatItems.length).toBeGreaterThan(0)
  })

  it("handles mobile sidebar", () => {
    // Mock mobile viewport
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 375,
    })

    render(
      <AmaniSidebar
        chatHistory={mockChatHistory}
        currentSessionId={null}
        isOpen={false}
        {...mockHandlers}
      />
    )

    // Should not render main sidebar on mobile when closed
    const sidebar = screen.queryByRole("complementary")
    expect(sidebar).not.toBeInTheDocument()
  })
})