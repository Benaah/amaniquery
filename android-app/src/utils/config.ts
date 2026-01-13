import {Platform} from 'react-native';

// For Android, localhost doesn't work - use 10.0.2.2 for emulator or actual IP for device
const getDefaultApiUrl = () => {
  if (__DEV__) {
    if (Platform.OS === 'android') {
      // Use 10.0.2.2 for Android emulator, or set your actual IP for physical device
      return 'http://10.0.2.2:8000';
    }
    return 'http://localhost:8000';
  }
  // In production, use environment variable or default
  return process.env.API_BASE_URL || 'https://api.amaniquery.com';
};

export const API_BASE_URL = getDefaultApiUrl();

export const ENABLE_NOTIFICATIONS =
  process.env.ENABLE_NOTIFICATIONS !== 'false';
