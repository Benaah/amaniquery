import {useState, useCallback, useEffect} from 'react';
import {Message, ChatSession} from '../types';
import {chatAPI} from '../api/chat';
import {storage} from '../utils/storage';
import {useStreamingResponse} from './useStreamingResponse';

export function useChat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const streamResponse = useStreamingResponse();

  // Load current session from storage
  useEffect(() => {
    const loadSession = async () => {
      const sessionId = await storage.getCurrentSessionId();
      if (sessionId) {
        setCurrentSessionId(sessionId);
        await loadMessages(sessionId);
      }
    };
    loadSession();
  }, []);

  const loadSessions = useCallback(async () => {
    try {
      const data = await chatAPI.getSessions();
      setSessions(data);
    } catch (err) {
      console.error('Failed to load sessions:', err);
    }
  }, []);

  const loadMessages = useCallback(async (sessionId: string) => {
    try {
      const data = await chatAPI.getMessages(sessionId);
      setMessages(data);
    } catch (err) {
      console.error('Failed to load messages:', err);
      setError(err instanceof Error ? err.message : 'Failed to load messages');
    }
  }, []);

  const createNewSession = useCallback(async (title?: string): Promise<string | null> => {
    try {
      const session = await chatAPI.createSession(title);
      setCurrentSessionId(session.id);
      await storage.setCurrentSessionId(session.id);
      setMessages([]);
      await loadSessions();
      return session.id;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create session');
      return null;
    }
  }, [loadSessions]);

  const sendMessage = useCallback(
    async (content: string, useStreaming: boolean = true) => {
      if (!content.trim()) return;

      let sessionId = currentSessionId;
      if (!sessionId) {
        sessionId = await createNewSession(content.trim().substring(0, 50));
        if (!sessionId) return;
      }

      const userMessage: Message = {
        id: Date.now().toString(),
        session_id: sessionId,
        role: 'user',
        content: content.trim(),
        created_at: new Date().toISOString(),
        saved: false,
      };

      setMessages(prev => [...prev, userMessage]);
      setIsLoading(true);
      setError(null);

      try {
        if (useStreaming) {
          streamResponse.startStream();

          const assistantMessageId = (Date.now() + 1).toString();
          const assistantMessage: Message = {
            id: assistantMessageId,
            session_id: sessionId,
            role: 'assistant',
            content: '',
            created_at: new Date().toISOString(),
            saved: false,
          };
          setMessages(prev => [...prev, assistantMessage]);

          await chatAPI.sendMessage(
            sessionId,
            content.trim(),
            (chunk) => {
              streamResponse.appendChunk(chunk);
              setMessages(prev =>
                prev.map(msg =>
                  msg.id === assistantMessageId
                    ? {...msg, content: streamResponse.content + chunk}
                    : msg,
                ),
              );
            },
            (metadata) => {
              streamResponse.completeStream(metadata);
              setMessages(prev =>
                prev.map(msg =>
                  msg.id === assistantMessageId
                    ? {
                        ...msg,
                        content: streamResponse.content,
                        sources: metadata?.sources,
                        model_used: metadata?.model_used,
                        token_count: metadata?.token_count,
                      }
                    : msg,
                ),
              );
            },
          );
        } else {
          // Non-streaming fallback
          await chatAPI.sendMessage(sessionId, content.trim());
          await loadMessages(sessionId);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to send message');
        setMessages(prev =>
          prev.map(msg =>
            msg.id === userMessage.id ? {...msg, failed: true} : msg,
          ),
        );
      } finally {
        setIsLoading(false);
      }
    },
    [currentSessionId, createNewSession, streamResponse, loadMessages],
  );

  const submitFeedback = useCallback(
    async (messageId: string, feedbackType: 'like' | 'dislike') => {
      try {
        await chatAPI.submitFeedback(messageId, feedbackType);
        setMessages(prev =>
          prev.map(msg =>
            msg.id === messageId
              ? {...msg, feedback_type: feedbackType}
              : msg,
          ),
        );
      } catch (err) {
        console.error('Failed to submit feedback:', err);
      }
    },
    [],
  );

  return {
    messages,
    currentSessionId,
    sessions,
    isLoading,
    error,
    sendMessage,
    createNewSession,
    loadSessions,
    loadMessages,
    submitFeedback,
  };
}

