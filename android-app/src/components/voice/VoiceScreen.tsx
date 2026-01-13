import React from 'react';
import {View, Text, StyleSheet} from 'react-native';

export const VoiceScreen: React.FC = () => {
  return (
    <View style={styles.container}>
      <Text style={styles.text}>Voice Chat is currently being updated to use VibeVoice.</Text>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#FFFFFF',
  },
  text: {
    fontSize: 16,
    color: '#666',
    textAlign: 'center',
    padding: 20,
  },
});