import React, {useRef, useEffect, useMemo} from 'react';
import {FlatList, StyleSheet, View, Text} from 'react-native';
import {Message} from '../../types';
import {MessageBubble} from './MessageBubble';

interface MessageListProps {
  messages: Message[];
  onFeedback?: (messageId: string, type: 'like' | 'dislike') => void;
  onEdit?: (messageId: string) => void;
  onRegenerate?: (messageId: string) => void;
}

interface ListItem {
  type: 'message' | 'dateSeparator';
  id: string;
  message?: Message;
  date?: string;
  showAvatar?: boolean;
}

export const MessageList: React.FC<MessageListProps> = ({
  messages,
  onFeedback,
  onEdit,
  onRegenerate,
}) => {
  const flatListRef = useRef<FlatList>(null);

  const listItems = useMemo(() => {
    const items: ListItem[] = [];
    let prevMessage: Message | null = null;

    messages.forEach((message, index) => {
      // Check if we need a date separator
      const showDateSeparator =
        !prevMessage ||
        new Date(message.created_at).toDateString() !==
          new Date(prevMessage.created_at).toDateString();

      if (showDateSeparator) {
        items.push({
          type: 'dateSeparator',
          id: `date-${message.created_at}`,
          date: new Date(message.created_at).toLocaleDateString(undefined, {
            weekday: 'long',
            year: 'numeric',
            month: 'long',
            day: 'numeric',
          }),
        });
      }

      // Determine if avatar should be shown
      const showAvatar =
        !prevMessage ||
        prevMessage.role !== message.role ||
        new Date(message.created_at).getTime() -
          new Date(prevMessage.created_at).getTime() >
          300000; // 5 minutes

      items.push({
        type: 'message',
        id: message.id,
        message,
        showAvatar,
      });

      prevMessage = message;
    });

    return items;
  }, [messages]);

  useEffect(() => {
    if (messages.length > 0) {
      setTimeout(() => {
        flatListRef.current?.scrollToEnd({animated: true});
      }, 100);
    }
  }, [messages]);

  const renderItem = ({item}: {item: ListItem}) => {
    if (item.type === 'dateSeparator') {
      return (
        <View style={styles.dateSeparator}>
          <View style={styles.dateSeparatorLine} />
          <Text style={styles.dateSeparatorText}>{item.date}</Text>
          <View style={styles.dateSeparatorLine} />
        </View>
      );
    }

    if (item.type === 'message' && item.message) {
      return (
        <MessageBubble
          message={item.message}
          onFeedback={onFeedback}
          onEdit={onEdit}
          onRegenerate={onRegenerate}
          showAvatar={item.showAvatar}
        />
      );
    }

    return null;
  };

  return (
    <FlatList
      ref={flatListRef}
      data={listItems}
      keyExtractor={item => item.id}
      renderItem={renderItem}
      contentContainerStyle={styles.contentContainer}
      style={styles.list}
      onContentSizeChange={() => {
        flatListRef.current?.scrollToEnd({animated: true});
      }}
    />
  );
};

const styles = StyleSheet.create({
  list: {
    flex: 1,
  },
  contentContainer: {
    paddingVertical: 24,
    paddingBottom: 40, // Add extra padding at bottom
  },
  dateSeparator: {
    flexDirection: 'row',
    alignItems: 'center',
    marginVertical: 16,
    paddingHorizontal: 16,
  },
  dateSeparatorLine: {
    flex: 1,
    height: 1,
    backgroundColor: '#E9ECEF',
  },
  dateSeparatorText: {
    fontSize: 12,
    color: '#999',
    paddingHorizontal: 12,
    backgroundColor: '#FFFFFF',
  },
});
