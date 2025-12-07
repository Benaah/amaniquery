/**
 * Media API Client
 * Handles multimodal media uploads and asset management
 * Integrates with /api/v1/media/* endpoints
 */

import type { MediaFileType, MediaAsset, MediaMetadata, MediaProcessingStatus } from "./types"

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

// ============================================================
// Types (re-export from types.ts for convenience)
// ============================================================

// Re-export types that consumers might need
export type { MediaFileType, MediaAsset, MediaMetadata, MediaProcessingStatus }

// Additional API-specific types
export type ProcessingStatus = MediaProcessingStatus

export interface MediaUploadResponse {
  asset_id: string
  session_id: string
  file_type: MediaFileType
  filename: string
  status: ProcessingStatus
  cloudinary_url?: string
  processing_time_ms?: number
  transcript?: string
  frame_urls?: string[]
  embedding_dimensions?: number
  metadata?: MediaMetadata
}

export interface ProcessingStatusResponse {
  asset_id: string
  status: ProcessingStatus
  progress_percent?: number
  current_step?: string
  error_message?: string
}

export interface MediaQueryResponse {
  response: string
  sources?: Array<{
    asset_id: string
    relevance_score: number
    excerpt?: string
  }>
  processing_time_ms: number
}

// ============================================================
// Helper Functions
// ============================================================

function getAuthHeaders(): Record<string, string> {
  const headers: Record<string, string> = {}
  
  if (typeof window !== "undefined") {
    const sessionToken = localStorage.getItem("session_token")
    if (sessionToken) {
      headers["X-Session-Token"] = sessionToken
    }
  }
  
  return headers
}

function detectFileType(file: File): MediaFileType {
  const mimeType = file.type.toLowerCase()
  
  if (mimeType.startsWith("image/")) return "image"
  if (mimeType === "application/pdf") return "pdf"
  if (mimeType.startsWith("audio/")) return "audio"
  if (mimeType.startsWith("video/")) return "video"
  
  // Fallback to extension check
  const ext = file.name.split(".").pop()?.toLowerCase()
  if (["jpg", "jpeg", "png", "gif", "webp", "bmp"].includes(ext || "")) return "image"
  if (ext === "pdf") return "pdf"
  if (["mp3", "wav", "m4a", "ogg", "flac", "aac"].includes(ext || "")) return "audio"
  if (["mp4", "mov", "avi", "mkv", "webm", "m4v"].includes(ext || "")) return "video"
  
  return "image" // Default fallback
}

// ============================================================
// Media API Client Class
// ============================================================

export class MediaApiClient {
  private baseURL: string

  constructor(baseURL: string = API_BASE_URL) {
    this.baseURL = baseURL
  }

  /**
   * Upload a media file with automatic type detection
   */
  async upload(
    file: File,
    sessionId: string,
    options?: {
      onProgress?: (percent: number) => void
      extractFrames?: boolean
      transcribe?: boolean
    }
  ): Promise<MediaUploadResponse> {
    const formData = new FormData()
    formData.append("file", file)
    formData.append("session_id", sessionId)
    
    if (options?.extractFrames !== undefined) {
      formData.append("extract_frames", String(options.extractFrames))
    }
    if (options?.transcribe !== undefined) {
      formData.append("transcribe", String(options.transcribe))
    }

    const response = await fetch(`${this.baseURL}/api/v1/media/upload`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: formData,
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: "Upload failed" }))
      throw new Error(error.detail || `HTTP ${response.status}`)
    }

    return response.json()
  }

  /**
   * Upload an image file
   */
  async uploadImage(file: File, sessionId: string): Promise<MediaUploadResponse> {
    const formData = new FormData()
    formData.append("file", file)
    formData.append("session_id", sessionId)

    const response = await fetch(`${this.baseURL}/api/v1/media/upload/image`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: formData,
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: "Image upload failed" }))
      throw new Error(error.detail || `HTTP ${response.status}`)
    }

    return response.json()
  }

  /**
   * Upload a PDF file
   */
  async uploadPdf(file: File, sessionId: string): Promise<MediaUploadResponse> {
    const formData = new FormData()
    formData.append("file", file)
    formData.append("session_id", sessionId)

    const response = await fetch(`${this.baseURL}/api/v1/media/upload/pdf`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: formData,
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: "PDF upload failed" }))
      throw new Error(error.detail || `HTTP ${response.status}`)
    }

    return response.json()
  }

  /**
   * Upload an audio file
   */
  async uploadAudio(
    file: File,
    sessionId: string,
    options?: { transcribe?: boolean }
  ): Promise<MediaUploadResponse> {
    const formData = new FormData()
    formData.append("file", file)
    formData.append("session_id", sessionId)
    
    if (options?.transcribe !== undefined) {
      formData.append("transcribe", String(options.transcribe))
    }

    const response = await fetch(`${this.baseURL}/api/v1/media/upload/audio`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: formData,
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: "Audio upload failed" }))
      throw new Error(error.detail || `HTTP ${response.status}`)
    }

    return response.json()
  }

  /**
   * Upload a video file
   */
  async uploadVideo(
    file: File,
    sessionId: string,
    options?: { extractFrames?: boolean; transcribeAudio?: boolean }
  ): Promise<MediaUploadResponse> {
    const formData = new FormData()
    formData.append("file", file)
    formData.append("session_id", sessionId)
    
    if (options?.extractFrames !== undefined) {
      formData.append("extract_frames", String(options.extractFrames))
    }
    if (options?.transcribeAudio !== undefined) {
      formData.append("transcribe_audio", String(options.transcribeAudio))
    }

    const response = await fetch(`${this.baseURL}/api/v1/media/upload/video`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: formData,
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: "Video upload failed" }))
      throw new Error(error.detail || `HTTP ${response.status}`)
    }

    return response.json()
  }

  /**
   * Get all assets for a session
   */
  async getSessionAssets(sessionId: string): Promise<MediaAsset[]> {
    const response = await fetch(
      `${this.baseURL}/api/v1/media/sessions/${sessionId}/assets`,
      {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
          ...getAuthHeaders(),
        },
      }
    )

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: "Failed to get assets" }))
      throw new Error(error.detail || `HTTP ${response.status}`)
    }

    return response.json()
  }

  /**
   * Get a specific asset by ID
   */
  async getAsset(assetId: string): Promise<MediaAsset> {
    const response = await fetch(`${this.baseURL}/api/v1/media/assets/${assetId}`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
        ...getAuthHeaders(),
      },
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: "Failed to get asset" }))
      throw new Error(error.detail || `HTTP ${response.status}`)
    }

    return response.json()
  }

  /**
   * Re-process an asset (e.g., re-run transcription)
   */
  async reprocessAsset(assetId: string): Promise<MediaUploadResponse> {
    const response = await fetch(`${this.baseURL}/api/v1/media/process/${assetId}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...getAuthHeaders(),
      },
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: "Failed to reprocess asset" }))
      throw new Error(error.detail || `HTTP ${response.status}`)
    }

    return response.json()
  }

  /**
   * Delete an asset
   */
  async deleteAsset(assetId: string): Promise<void> {
    const response = await fetch(`${this.baseURL}/api/v1/media/assets/${assetId}`, {
      method: "DELETE",
      headers: {
        "Content-Type": "application/json",
        ...getAuthHeaders(),
      },
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: "Failed to delete asset" }))
      throw new Error(error.detail || `HTTP ${response.status}`)
    }
  }
}

// ============================================================
// Singleton Instance
// ============================================================

export const mediaApi = new MediaApiClient()

// ============================================================
// Utility Functions
// ============================================================

/**
 * Check if a file type is supported for media upload
 */
export function isSupportedMediaType(file: File): boolean {
  const type = detectFileType(file)
  return ["image", "pdf", "audio", "video"].includes(type)
}

/**
 * Get file type from File object
 */
export function getMediaFileType(file: File): MediaFileType {
  return detectFileType(file)
}

/**
 * Get human-readable file type label
 */
export function getFileTypeLabel(type: MediaFileType): string {
  const labels: Record<MediaFileType, string> = {
    image: "Image",
    pdf: "PDF Document",
    audio: "Audio",
    video: "Video",
  }
  return labels[type]
}

/**
 * Get accepted file extensions for input element
 */
export function getAcceptedMediaExtensions(): string {
  return [
    // Images
    ".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp",
    // PDFs
    ".pdf",
    // Audio
    ".mp3", ".wav", ".m4a", ".ogg", ".flac", ".aac",
    // Video
    ".mp4", ".mov", ".avi", ".mkv", ".webm", ".m4v",
  ].join(",")
}

/**
 * Format file size for display
 */
export function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  return `${(bytes / (1024 * 1024 * 1024)).toFixed(2)} GB`
}

/**
 * Format duration in seconds to mm:ss or hh:mm:ss
 */
export function formatDuration(seconds: number): string {
  const hrs = Math.floor(seconds / 3600)
  const mins = Math.floor((seconds % 3600) / 60)
  const secs = Math.floor(seconds % 60)
  
  if (hrs > 0) {
    return `${hrs}:${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`
  }
  return `${mins}:${secs.toString().padStart(2, "0")}`
}
