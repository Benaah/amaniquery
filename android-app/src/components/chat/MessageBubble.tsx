import React, {useEffect} from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Clipboard,
  Alert,
} from 'react-native';
import Animated, {
  useAnimatedStyle,
  useSharedValue,
  withTiming,
  withSpring,
} from 'react-native-reanimated';
import Icon from 'react-native-vector-icons/Ionicons';
import {Message} from '../../types';
import {MarkdownRenderer} from '../common/MarkdownRenderer';
import {SourceCard} from './SourceCard';

interface MessageBubbleProps {
  message: Message;
  onFeedback?: (messageId: string, type: 'like' | 'dislike') => void;
  onEdit?: (messageId: string) => void;
  onRegenerate?: (messageId: string) => void;
  showAvatar?: boolean;
}

export const MessageBubble: React.FC<MessageBubbleProps> = ({
  message,
  onFeedback,
  onEdit,
  onRegenerate,
  showAvatar = true,
}) => {
  const isUser = message.role === 'user';
  const opacity = useSharedValue(0);
  const translateY = useSharedValue(20);

  useEffect(() => {
    opacity.value = withTiming(1, {duration: 300});
    translateY.value = withSpring(0, {
      damping: 15,
      stiffness: 150,
    });
  }, [opacity, translateY]);

  const animatedStyle = useAnimatedStyle(() => {
    return {
      opacity: opacity.value,
      transform: [{translateY: translateY.value}],
    };
  });

  const handleCopy = () => {
    Clipboard.setString(message.content);
    Alert.alert('Copied', 'Message copied to clipboard');
  };

  const formatTimestamp = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleTimeString([], {hour: '2-digit', minute: '2-digit'});
  };

  return (
    <Animated.View
      style={[
        styles.container,
        isUser ? styles.userContainer : styles.assistantContainer,
        animatedStyle,
      ]}>
      {showAvatar && !isUser && (
        <View style={styles.avatar}>
          <Icon name="chatbubbles" size={16} color="#007AFF" />
        </View>
      )}
      {showAvatar && isUser && <View style={styles.avatarSpacer} />}
      <View style={styles.bubbleWrapper}>
        <View
          style={[
            styles.bubble,
            isUser ? styles.userBubble : styles.assistantBubble,
            message.failed && styles.failedBubble,
          ]}>
          {message.attachments && message.attachments.length > 0 && (
            <View style={styles.attachmentsContainer}>
              {message.attachments.map(attachment => (
                <View key={attachment.id} style={styles.attachmentItem}>
                  <Icon
                    name={
                      attachment.file_type === 'pdf'
                        ? 'document-text'
                        : attachment.file_type === 'image'
                        ? 'image'
                        : 'document'
                    }
                    size={20}
                    color={isUser ? '#FFFFFF' : '#007AFF'}
                  />
                  <View style={styles.attachmentInfo}>
                    <Text
                      style={[
                        styles.attachmentName,
                        isUser && styles.attachmentNameUser,
                      ]}
                      numberOfLines={1}>
                      {attachment.filename}
                    </Text>
                    <Text
                      style={[
                        styles.attachmentSize,
                        isUser && styles.attachmentSizeUser,
                      ]}>
                      {(attachment.file_size / 1024).toFixed(1)} KB •{' '}
                      {attachment.file_type}
                    </Text>
                  </View>
                  {attachment.processed && (
                    <View style={styles.processedBadge}>
                      <Text style={styles.processedText}>✓</Text>
                    </View>
                  )}
                </View>
              ))}
            </View>
          )}

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

        <View style={styles.metadata}>
          <Text style={styles.timestamp}>
            {formatTimestamp(message.created_at)}
          </Text>
          {message.model_used && (
            <Text style={styles.modelInfo}>{message.model_used}</Text>
          )}
        </View>
      </View>

      {!isUser && !message.failed && (
        <View style={styles.actionContainer}>
          {onRegenerate && (
            <TouchableOpacity
              onPress={() => onRegenerate(message.id)}
              style={styles.actionButton}
              disabled={message.isRegenerating}>
              <Icon
                name="refresh"
                size={16}
                color={message.isRegenerating ? '#999' : '#007AFF'}
              />
              <Text
                style={[
                  styles.actionText,
                  message.isRegenerating && styles.actionTextDisabled,
                ]}>
                Regenerate
              </Text>
            </TouchableOpacity>
          )}
          {onFeedback && (
            <>
              <TouchableOpacity
                onPress={() => onFeedback(message.id, 'like')}
                style={[
                  styles.actionButton,
                  message.feedback_type === 'like' && styles.actionButtonActive,
                ]}>
                <Icon
                  name="thumbs-up"
                  size={16}
                  color={message.feedback_type === 'like' ? '#28A745' : '#666'}
                />
              </TouchableOpacity>
              <TouchableOpacity
                onPress={() => onFeedback(message.id, 'dislike')}
                style={[
                  styles.actionButton,
                  message.feedback_type === 'dislike' &&
                    styles.actionButtonActive,
                ]}>
                <Icon
                  name="thumbs-down"
                  size={16}
                  color={
                    message.feedback_type === 'dislike' ? '#DC3545' : '#666'
                  }
                />
              </TouchableOpacity>
            </>
          )}
          <TouchableOpacity onPress={handleCopy} style={styles.actionButton}>
            <Icon name="copy" size={16} color="#666" />
          </TouchableOpacity>
        </View>
      )}

      {isUser && !message.failed && onEdit && (
        <View style={styles.actionContainer}>
          <TouchableOpacity
            onPress={() => onEdit(message.id)}
            style={styles.actionButton}>
            <Icon name="create-outline" size={16} color="#666" />
            <Text style={styles.actionText}>Edit</Text>
          </TouchableOpacity>
          <TouchableOpacity onPress={handleCopy} style={styles.actionButton}>
            <Icon name="copy" size={16} color="#666" />
          </TouchableOpacity>
        </View>
      )}

      {message.failed && (
        <View style={styles.errorContainer}>
          <Text style={styles.errorText}>Failed to send</Text>
          {onEdit && isUser && (
            <TouchableOpacity
              onPress={() => onEdit(message.id)}
              style={styles.retryButton}>
              <Text style={styles.retryText}>Retry</Text>
            </TouchableOpacity>
          )}
        </View>
      )}
    </Animated.View>
  );
};

const styles = StyleSheet.create({
  container: {
    marginVertical: 4,
    paddingHorizontal: 16,
    flexDirection: 'row',
  },
  userContainer: {
    justifyContent: 'flex-end',
  },
  assistantContainer: {
    justifyContent: 'flex-start',
  },
  avatar: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: '#F1F3F5',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 8,
    marginTop: 4,
  },
  avatarSpacer: {
    width: 32,
    marginLeft: 8,
  },
  bubbleWrapper: {
    flex: 1,
    maxWidth: '85%',
  },
  bubble: {
    padding: 14,
    borderRadius: 20,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 1,
    },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
  },
  userBubble: {
    backgroundColor: '#007AFF',
    borderBottomRightRadius: 4,
  },
  assistantBubble: {
    backgroundColor: '#F8F9FA',
    borderBottomLeftRadius: 4,
  },
  failedBubble: {
    borderWidth: 1,
    borderColor: '#DC3545',
    backgroundColor: '#FFF5F5',
  },
  userText: {
    color: '#FFFFFF',
    fontSize: 16,
    lineHeight: 24,
  },
  metadata: {
    flexDirection: 'row',
    marginTop: 6,
    gap: 8,
    alignItems: 'center',
  },
  timestamp: {
    fontSize: 11,
    color: '#999',
  },
  modelInfo: {
    fontSize: 11,
    color: '#999',
    fontFamily: 'monospace',
  },
  sourcesContainer: {
    marginTop: 8,
    width: '100%',
  },
  actionContainer: {
    flexDirection: 'row',
    marginTop: 6,
    gap: 12,
    alignItems: 'center',
  },
  actionButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 4,
    paddingHorizontal: 8,
    gap: 4,
  },
  actionButtonActive: {
    backgroundColor: '#F0F0F0',
    borderRadius: 8,
  },
  actionText: {
    fontSize: 13,
    color: '#666',
  },
  actionTextDisabled: {
    color: '#999',
  },
  errorContainer: {
    flexDirection: 'row',
    marginTop: 6,
    alignItems: 'center',
    gap: 8,
  },
  errorText: {
    fontSize: 13,
    color: '#DC3545',
  },
  retryButton: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    backgroundColor: '#DC3545',
    borderRadius: 12,
  },
  retryText: {
    color: '#FFFFFF',
    fontSize: 13,
    fontWeight: '600',
  },
  attachmentsContainer: {
    marginBottom: 8,
    gap: 8,
  },
  attachmentItem: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 8,
    borderRadius: 8,
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
  },
  attachmentInfo: {
    flex: 1,
    marginLeft: 8,
  },
  attachmentName: {
    fontSize: 14,
    fontWeight: '500',
    color: '#000',
  },
  attachmentNameUser: {
    color: '#FFFFFF',
  },
  attachmentSize: {
    fontSize: 12,
    color: '#666',
    marginTop: 2,
  },
  attachmentSizeUser: {
    color: 'rgba(255, 255, 255, 0.8)',
  },
  processedBadge: {
    width: 20,
    height: 20,
    borderRadius: 10,
    backgroundColor: '#28A745',
    justifyContent: 'center',
    alignItems: 'center',
  },
  processedText: {
    color: '#FFFFFF',
    fontSize: 12,
    fontWeight: 'bold',
  },
});
