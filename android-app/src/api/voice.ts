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
    // Note: In React Native, we'll need to call a backend endpoint
    // that generates the LiveKit token, similar to the Next.js API route
    const response = await apiClient.post<VoiceTokenResponse>(
      '/api/livekit-token',
      {
        roomName,
        participantName,
        voice,
      },
    );
    return response.token;
  },
};

