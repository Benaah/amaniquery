import {apiClient} from './client';

export interface LoginResponse {
  session_token: string;
  user: User;
}

export interface User {
  id: string;
  email: string;
  name: string | null;
  status: string;
  email_verified: boolean;
  phone_verified?: boolean;
  last_login: string | null;
  profile_image_url?: string | null;
  created_at?: string;
  updated_at?: string;
  roles?: string[];
}

export interface RegisterRequest {
  email: string;
  password: string;
  name: string;
  phone_number: string;
}

export interface RegisterResponse {
  user: User;
}

export interface OTPRequest {
  phone_number: string;
  purpose: 'verification' | 'reset';
}

export interface OTPVerifyRequest {
  phone_number: string;
  otp: string;
  purpose: 'verification' | 'reset';
}

export const authAPI = {
  async login(email: string, password: string): Promise<LoginResponse> {
    return apiClient.post<LoginResponse>('/api/v1/auth/login', {
      email,
      password,
    });
  },

  async register(data: RegisterRequest): Promise<RegisterResponse> {
    return apiClient.post<RegisterResponse>('/api/v1/auth/register', data);
  },

  async logout(sessionToken: string): Promise<void> {
    return apiClient.post<void>(
      '/api/v1/auth/logout',
      {},
      {
        headers: {
          'X-Session-Token': sessionToken,
        },
      },
    );
  },

  async getCurrentUser(sessionToken: string): Promise<User> {
    return apiClient.get<User>('/api/v1/auth/me', {
      headers: {
        'X-Session-Token': sessionToken,
      },
    });
  },

  async sendOTP(data: OTPRequest): Promise<void> {
    return apiClient.post<void>('/api/v1/auth/phone/send-otp', data);
  },

  async verifyOTP(data: OTPVerifyRequest): Promise<void> {
    return apiClient.post<void>('/api/v1/auth/phone/verify-otp', data);
  },

  async forgotPassword(email: string): Promise<void> {
    return apiClient.post<void>('/api/v1/auth/forgot-password', {email});
  },

  async resetPassword(token: string, newPassword: string): Promise<void> {
    return apiClient.post<void>('/api/v1/auth/reset-password', {
      token,
      new_password: newPassword,
    });
  },
};
