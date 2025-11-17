import {apiClient} from './client';
import {NotificationSubscription, NotificationSource} from '../types';

export interface CreateSubscriptionRequest {
  phone_number: string;
  delivery_method: 'sms' | 'whatsapp';
  categories: string[];
  sources: string[];
}

export interface SubscriptionResponse {
  id: string;
  phone_number: string;
  delivery_method: 'sms' | 'whatsapp';
  categories: string[];
  sources: string[];
  active: boolean;
  created_at: string;
}

export interface NotificationSourcesResponse {
  sources: NotificationSource[];
}

export const notificationsAPI = {
  async getSources(): Promise<NotificationSource[]> {
    try {
      const response = await apiClient.get<NotificationSourcesResponse>(
        '/api/v1/notifications/sources',
      );
      return response.sources || [];
    } catch {
      // Fallback if endpoint doesn't exist
      return [];
    }
  },

  async createSubscription(
    data: CreateSubscriptionRequest,
  ): Promise<SubscriptionResponse> {
    // Map to backend format
    const payload = {
      phone_number: data.phone_number,
      notification_type: data.delivery_method === 'both' ? 'both' : data.delivery_method,
      schedule_type: 'immediate' as const,
      categories: data.categories.length > 0 ? data.categories : null,
      sources: data.sources.length > 0 ? data.sources : null,
    };
    return apiClient.post<SubscriptionResponse>(
      '/api/v1/notifications/subscribe',
      payload,
    );
  },

  async getSubscriptions(): Promise<SubscriptionResponse[]> {
    try {
      return apiClient.get<SubscriptionResponse[]>('/api/v1/notifications/subscriptions');
    } catch {
      return [];
    }
  },

  async getSubscription(id: string): Promise<SubscriptionResponse> {
    return apiClient.get<SubscriptionResponse>(`/api/v1/notifications/subscriptions/${id}`);
  },

  async updateSubscription(
    id: string,
    data: Partial<CreateSubscriptionRequest>,
  ): Promise<SubscriptionResponse> {
    const payload: any = {};
    if (data.phone_number) payload.phone_number = data.phone_number;
    if (data.delivery_method) payload.notification_type = data.delivery_method;
    if (data.categories) payload.categories = data.categories;
    if (data.sources) payload.sources = data.sources;
    return apiClient.put<SubscriptionResponse>(
      `/api/v1/notifications/subscriptions/${id}`,
      payload,
    );
  },

  async deleteSubscription(id: string): Promise<void> {
    return apiClient.delete(`/api/v1/notifications/subscriptions/${id}`);
  },
};

