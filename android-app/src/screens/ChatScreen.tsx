import React from 'react';
import {View, StyleSheet} from 'react-native';
import {ChatScreen as ChatScreenComponent} from '../components/chat/ChatScreen';

export const ChatScreen: React.FC = () => {
  return (
    <View style={styles.container}>
      <ChatScreenComponent />
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
});

