import React from 'react';
import {View, Text, StyleSheet, TouchableOpacity} from 'react-native';
import {Message} from '../../types';
import {MarkdownRenderer} from '../common/MarkdownRenderer';
import {SourceCard} from './SourceCard';

interface MessageBubbleProps {
  message: Message;
  onFeedback?: (messageId: string, type: 'like' | 'dislike') => void;
}

export const MessageBubble: React.FC<MessageBubbleProps> = ({
  message,
  onFeedback,
}) => {
  const isUser = message.role === 'user';

  return (
    <View
      style={[
        styles.container,
        isUser ? styles.userContainer : styles.assistantContainer,
      ]}>
      <View
        style={[
          styles.bubble,
          isUser ? styles.userBubble : styles.assistantBubble,
        ]}>
        {isUser ? (
          <Text style={styles.userText}>{message.content}</Text>
        ) : (
          <MarkdownRenderer content={message.content} />
        )}
      </View>

      {!isUser && message.sources && message.sources.length > 0 && (
        <View style={styles.sourcesContainer}>
          {message.sources.map((source, index) => (
            <SourceCard key={index} source={source} />
          ))}
        </View>
      )}

      {!isUser && onFeedback && (
        <View style={styles.feedbackContainer}>
          <TouchableOpacity
            onPress={() => onFeedback(message.id, 'like')}
            style={[
              styles.feedbackButton,
              message.feedback_type === 'like' && styles.feedbackButtonActive,
            ]}>
            <Text style={styles.feedbackText}>👍</Text>
          </TouchableOpacity>
          <TouchableOpacity
            onPress={() => onFeedback(message.id, 'dislike')}
            style={[
              styles.feedbackButton,
              message.feedback_type === 'dislike' && styles.feedbackButtonActive,
            ]}>
            <Text style={styles.feedbackText}>👎</Text>
          </TouchableOpacity>
        </View>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    marginVertical: 8,
    paddingHorizontal: 16,
  },
  userContainer: {
    alignItems: 'flex-end',
  },
  assistantContainer: {
    alignItems: 'flex-start',
  },
  bubble: {
    maxWidth: '80%',
    padding: 12,
    borderRadius: 16,
  },
  userBubble: {
    backgroundColor: '#007AFF',
  },
  assistantBubble: {
    backgroundColor: '#F1F3F5',
  },
  userText: {
    color: '#FFFFFF',
    fontSize: 16,
    lineHeight: 22,
  },
  sourcesContainer: {
    marginTop: 8,
    width: '100%',
  },
  feedbackContainer: {
    flexDirection: 'row',
    marginTop: 8,
    gap: 8,
  },
  feedbackButton: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
    backgroundColor: '#E9ECEF',
  },
  feedbackButtonActive: {
    backgroundColor: '#007AFF',
  },
  feedbackText: {
    fontSize: 16,
  },
});

