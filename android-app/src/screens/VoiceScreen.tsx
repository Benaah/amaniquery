import React from 'react';
import {View, StyleSheet} from 'react-native';
import {VoiceScreen as VoiceScreenComponent} from '../components/voice/VoiceScreen';

export const VoiceScreen: React.FC = () => {
  return (
    <View style={styles.container}>
      <VoiceScreenComponent />
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
});
