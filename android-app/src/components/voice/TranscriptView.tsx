import React from 'react';
import {View, Text, StyleSheet, ScrollView} from 'react-native';

export interface TranscriptMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  isStreaming?: boolean;
}

interface TranscriptViewProps {
  messages: TranscriptMessage[];
}

export const TranscriptView: React.FC<TranscriptViewProps> = ({messages}) => {
  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      {messages.map(message => (
        <View
          key={message.id}
          style={[
            styles.messageContainer,
            message.role === 'user'
              ? styles.userMessage
              : styles.assistantMessage,
          ]}>
          <Text style={styles.roleLabel}>
            {message.role === 'user' ? 'You' : 'Assistant'}
          </Text>
          <Text
            style={[
              styles.content,
              message.isStreaming && styles.streamingContent,
            ]}>
            {message.content}
            {message.isStreaming && <Text style={styles.cursor}>▋</Text>}
          </Text>
        </View>
      ))}
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F8F9FA',
  },
  content: {
    padding: 16,
  },
  messageContainer: {
    marginBottom: 16,
    padding: 12,
    borderRadius: 8,
  },
  userMessage: {
    backgroundColor: '#E3F2FD',
    alignSelf: 'flex-end',
    maxWidth: '80%',
  },
  assistantMessage: {
    backgroundColor: '#FFFFFF',
    alignSelf: 'flex-start',
    maxWidth: '80%',
  },
  roleLabel: {
    fontSize: 12,
    fontWeight: '600',
    color: '#666',
    marginBottom: 4,
  },
  content: {
    fontSize: 16,
    lineHeight: 22,
    color: '#212529',
  },
  streamingContent: {
    fontStyle: 'italic',
  },
  cursor: {
    color: '#007AFF',
  },
});
