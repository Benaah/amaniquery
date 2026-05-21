import {apiClient} from './client';
import {ResearchResult, StreamEvent} from '../types';

export const researchAPI = {
  async conductResearch(
    query: string,
    context?: Record<string, any>,
    generatePdf: boolean = true,
    generateDocx: boolean = true,
  ): Promise<ResearchResult> {
    const formData = new URLSearchParams();
    formData.append('query', query);
    if (context) {
      formData.append('context', JSON.stringify(context));
    }
    formData.append('generate_pdf', String(generatePdf));
    formData.append('generate_docx', String(generateDocx));

    const url = `${apiClient['baseURL']}/research/conduct`;

    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: formData.toString(),
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(error || 'Research request failed');
    }

    return response.json();
  },

  async streamResearch(
    sessionId: string,
    message: string,
    onEvent: (event: StreamEvent) => void,
    onComplete?: () => void,
  ): Promise<void> {
    return apiClient.stream(
      '/api/v1/chat/completions',
      {
        session_id: sessionId,
        message,
        is_research: true,
      },
      (chunk: string) => {
        try {
          const parsed = JSON.parse(chunk);
          onEvent(parsed as StreamEvent);
        } catch {
          // plain text chunk
          onEvent({type: 'content', content: chunk});
        }
      },
      () => {
        onComplete?.();
      },
    );
  },

  getDownloadUrl(bundleId: string, format: 'pdf' | 'docx'): string {
    const baseURL = (apiClient as any).baseURL || 'http://10.0.2.2:8000';
    return `${baseURL}/research/download/${bundleId}/${format}`;
  },
};
