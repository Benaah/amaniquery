import type { ReactNode } from "react"
import type { AmaniQueryResponse as StructuredResponse } from "../AmaniQueryResponse"

export type { StructuredResponse }

export interface WidgetInput {
    name: string
    label: string
    type: string
    placeholder?: string
    default_value?: string
}

export interface WidgetOutput {
    label: string
    format: string
}

export interface InteractiveWidget {
    type: string
    title: string
    description: string
    formula: string
    inputs: WidgetInput[]
    outputs: WidgetOutput[]
    source_citation?: string
}

export interface GithubDiff {
    old_text: string
    new_text: string
    title: string
    highlight_type: "side_by_side" | "unified"
}

export interface Message {
    id: string
    session_id: string
    role: "user" | "assistant"
    content: string
    created_at: string
    token_count?: number
    model_used?: string
    sources?: Source[]
    attachments?: Attachment[]
    feedback_type?: "like" | "dislike"
    saved?: boolean
    failed?: boolean
    originalQuery?: string
    isEditing?: boolean
    isRegenerating?: boolean
    // AK-RAG structured response support
    structured_response?: StructuredResponse
    interactive_widgets?: InteractiveWidget[]
    github_diff?: GithubDiff
    persona?: "wanjiku" | "wakili" | "mwanahabari"
}

export interface Source {
    title: string
    url: string
    source_name: string
    category: string
    excerpt: string
}

export interface Attachment {
    id: string
    filename: string
    file_type: string
    file_size: number
    uploaded_at: string
    processed: boolean
    cloudinary_url?: string
    // Media-specific fields
    transcript?: string
    frame_urls?: string[]
    duration_seconds?: number
    metadata?: {
        width?: number
        height?: number
        mime_type?: string
    }
}

export interface ChatSession {
    id: string
    title: string
    message_count: number
    created_at: string
    updated_at: string
}

export interface StreamMetadata {
    token_count?: number
    model_used?: string
    sources?: Source[]
}

export type SharePlatform = "twitter" | "linkedin" | "facebook" | "whatsapp" | "telegram" | "email" | "threads" | "bluesky" | "tiktok"

export interface ShareFormatResponse {
    platform: SharePlatform
    content: string | string[]
    character_count?: number
    hashtags?: string[]
    metadata?: Record<string, unknown>
}

export interface ShareSheetState {
    messageId: string
    platform: SharePlatform
    preview?: ShareFormatResponse | null
    isLoading: boolean
    shareLink?: string | null
    shareLinkLoading?: boolean
    posting?: boolean
    generatingImage?: boolean
    shareError?: string | null
    success?: string | null
}

export interface SharePlatformConfig {
    id: SharePlatform
    label: string
    accent: string
    description: string
    icon: ReactNode
}

// ============================================================
// Media Types (for multimodal RAG)
// ============================================================

export type MediaFileType = "image" | "pdf" | "audio" | "video"
export type MediaProcessingStatus = "pending" | "processing" | "completed" | "failed"

export interface MediaAsset {
    id: string
    session_id: string
    user_id?: string
    file_type: MediaFileType
    original_filename: string
    storage_path?: string
    cloudinary_url?: string
    transcript?: string
    metadata?: MediaMetadata
    processed: boolean
    created_at: string
}

export interface MediaMetadata {
    duration_seconds?: number
    frame_count?: number
    dimensions?: { width: number; height: number }
    audio_format?: string
    video_format?: string
    file_size_bytes?: number
    mime_type?: string
}

export interface MediaUploadResult {
    asset_id: string
    session_id: string
    file_type: MediaFileType
    filename: string
    status: MediaProcessingStatus
    cloudinary_url?: string
    processing_time_ms?: number
    transcript?: string
    frame_urls?: string[]
    embedding_dimensions?: number
    metadata?: MediaMetadata
}

export interface ProcessingProgress {
    asset_id: string
    status: MediaProcessingStatus
    progress_percent?: number
    current_step?: string
    error_message?: string
}

