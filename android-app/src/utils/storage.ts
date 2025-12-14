import AsyncStorage from '@react-native-async-storage/async-storage';

const STORAGE_KEYS = {
  CURRENT_SESSION_ID: '@amaniquery:current_session_id',
  CHAT_HISTORY: '@amaniquery:chat_history',
  NOTIFICATION_SUBSCRIPTIONS: '@amaniquery:notification_subscriptions',
  SESSION_TOKEN: '@amaniquery:session_token',
  USER_DATA: '@amaniquery:user_data',
  THEME_PREFERENCE: '@amaniquery:theme_preference',
  BIOMETRIC_ENABLED: '@amaniquery:biometric_enabled',
};

export const storage = {
  async getCurrentSessionId(): Promise<string | null> {
    return AsyncStorage.getItem(STORAGE_KEYS.CURRENT_SESSION_ID);
  },

  async setCurrentSessionId(sessionId: string): Promise<void> {
    return AsyncStorage.setItem(STORAGE_KEYS.CURRENT_SESSION_ID, sessionId);
  },

  async clearCurrentSessionId(): Promise<void> {
    return AsyncStorage.removeItem(STORAGE_KEYS.CURRENT_SESSION_ID);
  },

  async getChatHistory(): Promise<any[]> {
    const data = await AsyncStorage.getItem(STORAGE_KEYS.CHAT_HISTORY);
    return data ? JSON.parse(data) : [];
  },

  async saveChatHistory(history: any[]): Promise<void> {
    return AsyncStorage.setItem(
      STORAGE_KEYS.CHAT_HISTORY,
      JSON.stringify(history),
    );
  },

  async getSessionToken(): Promise<string | null> {
    return AsyncStorage.getItem(STORAGE_KEYS.SESSION_TOKEN);
  },

  async setSessionToken(token: string): Promise<void> {
    return AsyncStorage.setItem(STORAGE_KEYS.SESSION_TOKEN, token);
  },

  async clearSessionToken(): Promise<void> {
    return AsyncStorage.removeItem(STORAGE_KEYS.SESSION_TOKEN);
  },

  async getUserData(): Promise<any | null> {
    const data = await AsyncStorage.getItem(STORAGE_KEYS.USER_DATA);
    return data ? JSON.parse(data) : null;
  },

  async setUserData(user: any): Promise<void> {
    return AsyncStorage.setItem(STORAGE_KEYS.USER_DATA, JSON.stringify(user));
  },

  async clearUserData(): Promise<void> {
    return AsyncStorage.removeItem(STORAGE_KEYS.USER_DATA);
  },

  async getThemePreference(): Promise<string | null> {
    return AsyncStorage.getItem(STORAGE_KEYS.THEME_PREFERENCE);
  },

  async setThemePreference(theme: 'light' | 'dark'): Promise<void> {
    return AsyncStorage.setItem(STORAGE_KEYS.THEME_PREFERENCE, theme);
  },

  async getBiometricEnabled(): Promise<boolean> {
    const data = await AsyncStorage.getItem(STORAGE_KEYS.BIOMETRIC_ENABLED);
    return data === 'true';
  },

  async setBiometricEnabled(enabled: boolean): Promise<void> {
    return AsyncStorage.setItem(
      STORAGE_KEYS.BIOMETRIC_ENABLED,
      enabled.toString(),
    );
  },
};

