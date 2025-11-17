import {apiClient} from './client';
import {VoiceTokenResponse} from '../types';

export interface GenerateTokenRequest {
  roomName: string;
  participantName?: string;
  voice?: string;
}

export const voiceAPI = {
  async generateToken(
    roomName: string,
    participantName: string = 'user',
    voice?: string,
  ): Promise<string> {
    // Note: This endpoint should be added to the FastAPI backend
    // For now, we'll use a placeholder endpoint
    // The backend should implement: POST /api/livekit-token
    // Similar to the Next.js API route in frontend/src/app/api/livekit-token/route.ts
    try {
      const response = await apiClient.post<VoiceTokenResponse>(
        '/api/livekit-token',
        {
          roomName,
          participantName,
          voice,
        },
      );
      return response.token;
    } catch (error) {
      // Fallback: If endpoint doesn't exist, throw helpful error
      throw new Error(
        'LiveKit token endpoint not available. Please add POST /api/livekit-token to your FastAPI backend.',
      );
    }
  },
};

