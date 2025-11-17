import {useState, useCallback} from 'react';
import {StreamMetadata} from '../types';

export interface UseStreamingResponseReturn {
  content: string;
  metadata: StreamMetadata | null;
  isStreaming: boolean;
  startStream: () => void;
  appendChunk: (chunk: string) => void;
  completeStream: (metadata?: StreamMetadata) => void;
  reset: () => void;
}

export function useStreamingResponse(): UseStreamingResponseReturn {
  const [content, setContent] = useState('');
  const [metadata, setMetadata] = useState<StreamMetadata | null>(null);
  const [isStreaming, setIsStreaming] = useState(false);

  const startStream = useCallback(() => {
    setContent('');
    setMetadata(null);
    setIsStreaming(true);
  }, []);

  const appendChunk = useCallback((chunk: string) => {
    setContent(prev => prev + chunk);
  }, []);

  const completeStream = useCallback((streamMetadata?: StreamMetadata) => {
    setIsStreaming(false);
    if (streamMetadata) {
      setMetadata(streamMetadata);
    }
  }, []);

  const reset = useCallback(() => {
    setContent('');
    setMetadata(null);
    setIsStreaming(false);
  }, []);

  return {
    content,
    metadata,
    isStreaming,
    startStream,
    appendChunk,
    completeStream,
    reset,
  };
}

