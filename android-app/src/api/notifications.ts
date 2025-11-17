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
    const response = await apiClient.get<NotificationSourcesResponse>(
      '/notifications/sources',
    );
    return response.sources;
  },

  async createSubscription(
    data: CreateSubscriptionRequest,
  ): Promise<SubscriptionResponse> {
    return apiClient.post<SubscriptionResponse>(
      '/notifications/subscribe',
      data,
    );
  },

  async getSubscriptions(): Promise<SubscriptionResponse[]> {
    return apiClient.get<SubscriptionResponse[]>('/notifications/subscriptions');
  },

  async getSubscription(id: string): Promise<SubscriptionResponse> {
    return apiClient.get<SubscriptionResponse>(`/notifications/subscriptions/${id}`);
  },

  async updateSubscription(
    id: string,
    data: Partial<CreateSubscriptionRequest>,
  ): Promise<SubscriptionResponse> {
    return apiClient.put<SubscriptionResponse>(
      `/notifications/subscriptions/${id}`,
      data,
    );
  },

  async deleteSubscription(id: string): Promise<void> {
    return apiClient.delete(`/notifications/subscriptions/${id}`);
  },
};

