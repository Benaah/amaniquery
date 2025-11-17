import React from 'react';
import {View, StyleSheet, KeyboardAvoidingView, Platform} from 'react-native';
import {useChat} from '../../hooks/useChat';
import {MessageList} from './MessageList';
import {ChatInput} from './ChatInput';
import {ErrorMessage} from '../common/ErrorMessage';
import {LoadingSpinner} from '../common/LoadingSpinner';

export const ChatScreen: React.FC = () => {
  const {
    messages,
    isLoading,
    error,
    sendMessage,
    submitFeedback,
  } = useChat();

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      keyboardVerticalOffset={Platform.OS === 'ios' ? 0 : 20}>
      <View style={styles.content}>
        {error && (
          <ErrorMessage
            message={error}
            onDismiss={() => {
              // Error dismissal handled by hook
            }}
          />
        )}

        <MessageList messages={messages} onFeedback={submitFeedback} />

        {isLoading && messages.length === 0 && <LoadingSpinner />}
      </View>

      <ChatInput onSend={sendMessage} isLoading={isLoading} />
    </KeyboardAvoidingView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#FFFFFF',
  },
  content: {
    flex: 1,
  },
});

