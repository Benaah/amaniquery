import React, {
  useState,
  useEffect,
  useCallback,
  createContext,
  useContext,
} from 'react';
import {useColorScheme} from 'react-native';
import {storage} from '../utils/storage';

interface ThemeContextType {
  isDarkMode: boolean;
  toggleTheme: () => void;
  setDarkMode: (enabled: boolean) => void;
  colors: ThemeColors;
}

interface ThemeColors {
  background: string;
  surface: string;
  primary: string;
  text: string;
  textSecondary: string;
  border: string;
  error: string;
  success: string;
  warning: string;
}

const lightColors: ThemeColors = {
  background: '#FFFFFF',
  surface: '#F8F9FA',
  primary: '#007AFF',
  text: '#212529',
  textSecondary: '#6C757D',
  border: '#E9ECEF',
  error: '#DC3545',
  success: '#28A745',
  warning: '#FFC107',
};

const darkColors: ThemeColors = {
  background: '#121212',
  surface: '#1E1E1E',
  primary: '#2563EB',
  text: '#FFFFFF',
  textSecondary: '#9CA3AF',
  border: '#2D2D2D',
  error: '#EF4444',
  success: '#10B981',
  warning: '#F59E0B',
};

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export function useTheme(): ThemeContextType {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
}

interface ThemeProviderProps {
  children: React.ReactNode;
}

export function ThemeProvider({children}: ThemeProviderProps): React.JSX.Element {
  const systemColorScheme = useColorScheme();
  const [isDarkMode, setIsDarkMode] = useState(systemColorScheme === 'dark');

  useEffect(() => {
    loadThemePreference();
  }, []);

  const loadThemePreference = async () => {
    try {
      const savedTheme = await storage.getThemePreference();
      if (savedTheme !== null) {
        setIsDarkMode(savedTheme === 'dark');
      }
    } catch (error) {
      console.error('Failed to load theme preference:', error);
    }
  };

  const toggleTheme = useCallback(async () => {
    const newTheme = !isDarkMode;
    setIsDarkMode(newTheme);
    await storage.setThemePreference(newTheme ? 'dark' : 'light');
  }, [isDarkMode]);

  const setDarkMode = useCallback(async (enabled: boolean) => {
    setIsDarkMode(enabled);
    await storage.setThemePreference(enabled ? 'dark' : 'light');
  }, []);

  const colors = isDarkMode ? darkColors : lightColors;

  return (
    <ThemeContext.Provider
      value={{
        isDarkMode,
        toggleTheme,
        setDarkMode,
        colors,
      }}>
      {children}
    </ThemeContext.Provider>
  );
}
