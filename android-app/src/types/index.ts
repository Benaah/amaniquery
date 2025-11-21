export interface Attachment {
  id: string;
  filename: string;
  file_type: string;
  file_size: number;
  uploaded_at: string;
  processed: boolean;
}

export interface Message {
  id: string;
  session_id: string;
  role: 'user' | 'assistant';
  content: string;
  created_at: string;
  token_count?: number;
  model_used?: string;
  sources?: Source[];
  attachments?: Attachment[];
  feedback_type?: 'like' | 'dislike';
  saved?: boolean;
  failed?: boolean;
  isEditing?: boolean;
  isRegenerating?: boolean;
  originalQuery?: string;
}

export interface Source {
  title: string;
  url: string;
  source_name: string;
  category: string;
  excerpt: string;
}

export interface ChatSession {
  id: string;
  title: string;
  message_count: number;
  created_at: string;
  updated_at: string;
}

export interface StreamMetadata {
  token_count?: number;
  model_used?: string;
  sources?: Source[];
}

export interface NotificationSubscription {
  id?: string;
  phone_number: string;
  delivery_method: 'sms' | 'whatsapp';
  categories: string[];
  sources: string[];
  active: boolean;
}

export interface NotificationSource {
  name: string;
  article_count: number;
}

export interface VoiceTokenResponse {
  token: string;
}

export interface APIError {
  error: string;
  detail?: string;
}
