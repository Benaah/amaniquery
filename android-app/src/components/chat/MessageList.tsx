import React, {useRef, useEffect} from 'react';
import {FlatList, StyleSheet, View} from 'react-native';
import {Message} from '../../types';
import {MessageBubble} from './MessageBubble';

interface MessageListProps {
  messages: Message[];
  onFeedback?: (messageId: string, type: 'like' | 'dislike') => void;
}

export const MessageList: React.FC<MessageListProps> = ({
  messages,
  onFeedback,
}) => {
  const flatListRef = useRef<FlatList>(null);

  useEffect(() => {
    if (messages.length > 0) {
      setTimeout(() => {
        flatListRef.current?.scrollToEnd({animated: true});
      }, 100);
    }
  }, [messages]);

  return (
    <FlatList
      ref={flatListRef}
      data={messages}
      keyExtractor={item => item.id}
      renderItem={({item}) => (
        <MessageBubble message={item} onFeedback={onFeedback} />
      )}
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
    paddingVertical: 8,
  },
});

