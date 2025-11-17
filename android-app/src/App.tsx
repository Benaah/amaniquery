import React from 'react';
import {StatusBar, StyleSheet} from 'react-native';
import {AppNavigator} from './navigation/AppNavigator';
import 'react-native-gesture-handler';

const App: React.FC = () => {
  return (
    <>
      <StatusBar barStyle="dark-content" backgroundColor="#FFFFFF" />
      <AppNavigator />
    </>
  );
};

export default App;

