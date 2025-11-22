/**
 * Chat API Utilities
 * Handles session management and file uploads
 */

export async function createNewSession(
    firstMessage: string | undefined,
    API_BASE_URL: string,
    getAuthHeaders: () => Record<string, string>,
    setCurrentSessionId: (id: string) => void,
    setMessages: (messages: any[]) => void,
    loadChatHistory: () => void
): Promise<string | null> {
    // Generate title from first message if provided
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

export async function loadSession(
    sessionId: string,
    API_BASE_URL: string,
    getAuthHeaders: () => Record<string, string>,
    setMessages: (messages: any[]) => void,
    setCurrentSessionId: (id: string) => void,
    setShowHistory: (show: boolean) => void
): Promise<void> {
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

export async function uploadFiles(
    sessionId: string,
    files: File[],
    API_BASE_URL: string,
    getAuthHeaders: () => Record<string, string>,
    setUploadingFiles: (uploading: boolean) => void
): Promise<string[]> {
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
