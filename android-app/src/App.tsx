import React from 'react';
import {StatusBar} from 'react-native';
import {AppNavigator} from './navigation/AppNavigator';
import 'react-native-gesture-handler';
import Icon from 'react-native-vector-icons/Ionicons';

// Initialize vector icons
Icon.loadFont();

const App: React.FC = () => {
  return (
    <>
      <StatusBar barStyle="dark-content" backgroundColor="#FFFFFF" />
      <AppNavigator />
    </>
  );
};

export default App;

