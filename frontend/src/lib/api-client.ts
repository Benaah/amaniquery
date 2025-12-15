"use client"

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

/**
 *  Enhanced Query Options  
 */
export interface QueryOptions {
  knowledgeBases?: string[]  // kenya_law, kenya_news, parliament, general
  model?: string             // gemini-2.5-flash, gpt-4o-mini, gpt-4o, claude-3.5-sonnet
  useReranking?: boolean     // Enable intelligent re-ranking
  useHyDE?: boolean          // Enable HyDE query expansion
  temperature?: number       // LLM temperature (0-1)
  userId?: string            // User ID for profiling
}

export interface StreamCallback {
  onToken?: (token: string) => void
  onComplete?: (response: unknown) => void
  onError?: (error: Error) => void
}

export class ApiClient {
  private baseURL: string

  constructor(baseURL: string = API_URL) {
    this.baseURL = baseURL
  }

  private getHeaders(): HeadersInit {
    const headers: HeadersInit = {
      "Content-Type": "application/json",
    }

    // Add session token if available
    const sessionToken = localStorage.getItem("session_token")
    if (sessionToken) {
      headers["X-Session-Token"] = sessionToken
    }

    return headers
  }

  private getAuthOnlyHeaders(): HeadersInit {
    const headers: HeadersInit = {}

    // Add session token if available (no Content-Type for FormData)
    const sessionToken = localStorage.getItem("session_token")
    if (sessionToken) {
      headers["X-Session-Token"] = sessionToken
    }

    return headers
  }

  async get<T>(endpoint: string): Promise<T> {
    const response = await fetch(`${this.baseURL}${endpoint}`, {
      method: "GET",
      headers: this.getHeaders(),
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: "Request failed" }))
      throw new Error(error.detail || `HTTP ${response.status}`)
    }

    return response.json()
  }

  async post<T>(endpoint: string, data?: unknown): Promise<T> {
    const response = await fetch(`${this.baseURL}${endpoint}`, {
      method: "POST",
      headers: this.getHeaders(),
      body: data ? JSON.stringify(data) : undefined,
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: "Request failed" }))
      throw new Error(error.detail || `HTTP ${response.status}`)
    }

    return response.json()
  }

  async put<T>(endpoint: string, data?: unknown): Promise<T> {
    const response = await fetch(`${this.baseURL}${endpoint}`, {
      method: "PUT",
      headers: this.getHeaders(),
      body: data ? JSON.stringify(data) : undefined,
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: "Request failed" }))
      throw new Error(error.detail || `HTTP ${response.status}`)
    }

    return response.json()
  }

  async delete<T>(endpoint: string): Promise<T> {
    const response = await fetch(`${this.baseURL}${endpoint}`, {
      method: "DELETE",
      headers: this.getHeaders(),
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: "Request failed" }))
      throw new Error(error.detail || `HTTP ${response.status}`)
    }

    return response.json()
  }

  /**
   * Upload files using FormData (multipart/form-data)
   * Used for media uploads to /api/v1/media/* endpoints
   */
  async uploadFormData<T>(endpoint: string, formData: FormData): Promise<T> {
    const response = await fetch(`${this.baseURL}${endpoint}`, {
      method: "POST",
      headers: this.getAuthOnlyHeaders(), // No Content-Type - browser sets it with boundary
      body: formData,
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: "Upload failed" }))
      throw new Error(error.detail || `HTTP ${response.status}`)
    }

    return response.json()
  }

  /**
   * Upload a single file to the media API
   */
  async uploadFile<T>(
    endpoint: string,
    file: File,
    additionalFields?: Record<string, string>
  ): Promise<T> {
    const formData = new FormData()
    formData.append("file", file)

    if (additionalFields) {
      Object.entries(additionalFields).forEach(([key, value]) => {
        formData.append(key, value)
      })
    }

    return this.uploadFormData<T>(endpoint, formData)
  }
}

export const apiClient = new ApiClient()

