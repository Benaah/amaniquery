import React from 'react';
import {StatusBar} from 'react-native';
import {AppNavigator} from './navigation/AppNavigator';
import {AuthProvider} from './hooks/useAuth';
import 'react-native-gesture-handler';
import Icon from 'react-native-vector-icons/Ionicons';

// Initialize vector icons
Icon.loadFont();

const App: React.FC = () => {
  return (
    <AuthProvider>
      <StatusBar barStyle="dark-content" backgroundColor="#FFFFFF" />
      <AppNavigator />
    </AuthProvider>
  );
};

export default App;
