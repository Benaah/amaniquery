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

  return (
    <Animated.View
      style={[
        styles.container,
        isUser ? styles.userContainer : styles.assistantContainer,
        animatedStyle,
      ]}>
      {/* Assistant Avatar (Sparkles) */}
      {!isUser && showAvatar && (
        <View style={styles.avatarContainer}>
          {/* Using a star/sparkle icon to mimic Gemini */}
          <Icon name="sparkles" size={24} color="#4285F4" /> 
        </View>
      )}

      <View style={styles.contentWrapper}>
        <View
          style={[
            styles.bubble,
            isUser ? styles.userBubble : styles.assistantBubble,
            message.failed && styles.failedBubble,
          ]}>
          
          {/* Attachments */}
          {message.attachments && message.attachments.length > 0 && (
            <View style={styles.attachmentsContainer}>
              {message.attachments.map(attachment => (
                <View key={attachment.id} style={[
                  styles.attachmentItem,
                  isUser ? styles.attachmentItemUser : styles.attachmentItemAssistant
                ]}>
                  <Icon
                    name="document-text-outline"
                    size={20}
                    color={isUser ? '#FFFFFF' : '#444746'}
                  />
                  <Text
                    style={[
                      styles.attachmentName,
                      isUser ? styles.userText : styles.assistantText,
                    ]}
                    numberOfLines={1}>
                    {attachment.filename}
                  </Text>
                </View>
              ))}
            </View>
          )}

          {/* Message Content */}
          {isUser ? (
            <Text style={styles.userText}>{message.content}</Text>
          ) : (
            <MarkdownRenderer content={message.content} />
          )}
        </View>

        {/* Sources (Assistant Only) */}
        {!isUser && message.sources && message.sources.length > 0 && (
          <View style={styles.sourcesContainer}>
            {message.sources.map((source, index) => (
              <SourceCard key={index} source={source} />
            ))}
          </View>
        )}

        {/* Actions (Assistant Only) */}
        {!isUser && !message.failed && (
          <View style={styles.actionsRow}>
            {onFeedback && (
              <View style={styles.feedbackContainer}>
                <TouchableOpacity
                  onPress={() => onFeedback(message.id, 'like')}
                  style={styles.iconButton}>
                  <Icon
                    name={message.feedback_type === 'like' ? "thumbs-up" : "thumbs-up-outline"}
                    size={18}
                    color="#444746"
                  />
                </TouchableOpacity>
                <TouchableOpacity
                  onPress={() => onFeedback(message.id, 'dislike')}
                  style={styles.iconButton}>
                  <Icon
                    name={message.feedback_type === 'dislike' ? "thumbs-down" : "thumbs-down-outline"}
                    size={18}
                    color="#444746"
                  />
                </TouchableOpacity>
              </View>
            )}
            
            <TouchableOpacity onPress={handleCopy} style={styles.iconButton}>
              <Icon name="copy-outline" size={18} color="#444746" />
            </TouchableOpacity>
            
            {onRegenerate && (
              <TouchableOpacity onPress={() => onRegenerate(message.id)} style={styles.iconButton}>
                <Icon name="refresh-outline" size={18} color="#444746" />
              </TouchableOpacity>
            )}
          </View>
        )}
        
        {/* Failed State */}
        {message.failed && (
          <View style={styles.errorRow}>
            <Icon name="alert-circle" size={16} color="#DC3545" />
            <Text style={styles.errorText}>Failed to send</Text>
            {isUser && onEdit && (
              <TouchableOpacity onPress={() => onEdit(message.id)}>
                <Text style={styles.retryText}>Retry</Text>
              </TouchableOpacity>
            )}
          </View>
        )}
      </View>
    </Animated.View>
  );
};

const styles = StyleSheet.create({
  container: {
    marginVertical: 12,
    paddingHorizontal: 16,
    flexDirection: 'row',
    width: '100%',
  },
  userContainer: {
    justifyContent: 'flex-end',
  },
  assistantContainer: {
    justifyContent: 'flex-start',
  },
  avatarContainer: {
    marginRight: 12,
    paddingTop: 4,
  },
  contentWrapper: {
    flex: 1,
    maxWidth: '85%',
  },
  bubble: {
    borderRadius: 18,
    paddingVertical: 12,
    paddingHorizontal: 16,
  },
  userBubble: {
    backgroundColor: '#004A77', // Deep blue like Gemini User messages or #1F1F1F for dark mode look
    borderTopRightRadius: 4,
  },
  assistantBubble: {
    backgroundColor: 'transparent', // Transparent for assistant
    paddingHorizontal: 0, // Align text with avatar
    paddingVertical: 0,
  },
  failedBubble: {
    opacity: 0.7,
  },
  userText: {
    color: '#FFFFFF',
    fontSize: 16,
    lineHeight: 24,
  },
  assistantText: {
    color: '#1F1F1F', // Dark gray for text
    fontSize: 16,
    lineHeight: 24,
  },
  attachmentsContainer: {
    marginBottom: 8,
  },
  attachmentItem: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 8,
    borderRadius: 8,
    marginBottom: 4,
  },
  attachmentItemUser: {
    backgroundColor: 'rgba(255,255,255,0.1)',
  },
  attachmentItemAssistant: {
    backgroundColor: '#F0F4F9',
  },
  attachmentName: {
    marginLeft: 8,
    fontSize: 14,
  },
  sourcesContainer: {
    marginTop: 12,
  },
  actionsRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 8,
    gap: 16,
  },
  feedbackContainer: {
    flexDirection: 'row',
    gap: 16,
  },
  iconButton: {
    padding: 4,
  },
  errorRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 4,
    gap: 8,
  },
  errorText: {
    color: '#DC3545',
    fontSize: 12,
  },
  retryText: {
    color: '#004A77',
    fontSize: 12,
    fontWeight: 'bold',
  },
});