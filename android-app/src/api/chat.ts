import {apiClient} from './client';
import {Message, ChatSession, StreamMetadata, Source} from '../types';

export interface CreateSessionRequest {
  title?: string;
}

export interface CreateSessionResponse {
  id: string;
  title: string;
  created_at: string;
}

export interface SendMessageRequest {
  content: string;
  role: 'user';
  stream?: boolean;
  attachment_ids?: string[];
}

export interface UploadAttachmentResponse {
  attachment: {
    id: string;
    filename: string;
    file_type: string;
    file_size: number;
    uploaded_at: string;
    processed: boolean;
  };
  message: string;
}

export interface QueryRequest {
  query: string;
  top_k?: number;
  category?: string;
  include_sources?: boolean;
  stream?: boolean;
}

export interface QueryResponse {
  answer: string;
  sources?: Source[];
  query_time?: number;
  model_used?: string;
}

export const chatAPI = {
  async createSession(title?: string): Promise<CreateSessionResponse> {
    return apiClient.post<CreateSessionResponse>('/chat/sessions', {
      title: title || 'New Chat',
    });
  },

  async getSessions(): Promise<ChatSession[]> {
    return apiClient.get<ChatSession[]>('/chat/sessions');
  },

  async getSession(sessionId: string): Promise<ChatSession> {
    return apiClient.get<ChatSession>(`/chat/sessions/${sessionId}`);
  },

  async getMessages(sessionId: string): Promise<Message[]> {
    return apiClient.get<Message[]>(`/chat/sessions/${sessionId}/messages`);
  },

  async uploadAttachment(
    sessionId: string,
    fileUri: string,
    fileName: string,
    fileType: string,
  ): Promise<string> {
    const formData = new FormData();
    formData.append('file', {
      uri: fileUri,
      name: fileName,
      type: fileType,
    } as any);

    const response = await apiClient.postForm<UploadAttachmentResponse>(
      `/chat/sessions/${sessionId}/attachments`,
      formData,
    );
    return response.attachment.id;
  },

  async sendMessage(
    sessionId: string,
    content: string,
    onChunk?: (chunk: string) => void,
    onComplete?: (metadata?: StreamMetadata) => void,
    attachmentIds?: string[],
  ): Promise<void> {
    if (onChunk) {
      // Use streaming endpoint
      return apiClient.stream(
        `/chat/sessions/${sessionId}/messages`,
        {
          content,
          role: 'user',
          stream: true,
          attachment_ids: attachmentIds,
        },
        onChunk,
        onComplete,
      );
    } else {
      // Use non-streaming endpoint
      await apiClient.post(`/chat/sessions/${sessionId}/messages`, {
        content,
        role: 'user',
        stream: false,
        attachment_ids: attachmentIds,
      });
    }
  },

  async sendQuery(
    query: string,
    options?: {
      top_k?: number;
      category?: string;
      include_sources?: boolean;
      onChunk?: (chunk: string) => void;
      onComplete?: (metadata?: StreamMetadata) => void;
    },
  ): Promise<QueryResponse | void> {
    if (options?.onChunk) {
      // Use streaming query endpoint
      return apiClient.stream(
        '/stream/query',
        {
          query,
          top_k: options.top_k || 5,
          include_sources: options.include_sources !== false,
          stream: true,
        },
        options.onChunk,
        options.onComplete,
      );
    } else {
      // Use non-streaming endpoint
      return apiClient.post<QueryResponse>('/query', {
        query,
        top_k: options?.top_k || 5,
        category: options?.category,
        include_sources: options?.include_sources !== false,
      });
    }
  },

  async submitFeedback(
    messageId: string,
    feedbackType: 'like' | 'dislike',
  ): Promise<void> {
    return apiClient.post('/chat/feedback', {
      message_id: messageId,
      feedback_type: feedbackType,
    });
  },
};

