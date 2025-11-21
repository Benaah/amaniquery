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
