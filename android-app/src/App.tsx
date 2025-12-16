import React from 'react';
import {StatusBar} from 'react-native';
import {SafeAreaProvider} from 'react-native-safe-area-context';
import {AppNavigator} from './navigation/AppNavigator';
import {AuthProvider} from './hooks/useAuth';
import {ThemeProvider, useTheme} from './hooks/useTheme';
import {ErrorBoundary} from './components/common/ErrorBoundary';
import 'react-native-gesture-handler';
import Icon from 'react-native-vector-icons/Ionicons';

// Initialize vector icons
Icon.loadFont();

const AppContent: React.FC = () => {
  const {isDarkMode} = useTheme();

  return (
    <>
      <StatusBar
        barStyle={isDarkMode ? 'light-content' : 'dark-content'}
        backgroundColor={isDarkMode ? '#121212' : '#FFFFFF'}
      />
      <AppNavigator />
    </>
  );
};

const App: React.FC = () => {
  return (
    <ErrorBoundary>
      <SafeAreaProvider>
        <ThemeProvider>
          <AuthProvider>
            <AppContent />
          </AuthProvider>
        </ThemeProvider>
      </SafeAreaProvider>
    </ErrorBoundary>
  );
};

export default App;

