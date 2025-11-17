import React, {useState} from 'react';
import {View, StyleSheet, KeyboardAvoidingView, Platform, Alert} from 'react-native';
import {DocumentPickerResponse} from 'react-native-document-picker';
import {useChat} from '../../hooks/useChat';
import {chatAPI} from '../../api/chat';
import {MessageList} from './MessageList';
import {ChatInput} from './ChatInput';
import {ErrorMessage} from '../common/ErrorMessage';
import {LoadingSpinner} from '../common/LoadingSpinner';

export const ChatScreen: React.FC = () => {
  const [selectedFiles, setSelectedFiles] = useState<DocumentPickerResponse[]>([]);
  const [uploadingFiles, setUploadingFiles] = useState(false);
  const {
    messages,
    currentSessionId,
    isLoading,
    error,
    sendMessage,
    submitFeedback,
    createNewSession,
  } = useChat();

  const handleSend = async (message: string, attachmentIds?: string[]) => {
    // Upload files first if any
    let finalAttachmentIds = attachmentIds || [];
    if (selectedFiles.length > 0) {
      try {
        setUploadingFiles(true);
        let sessionId = currentSessionId;
        if (!sessionId) {
          sessionId = await createNewSession(message.trim().substring(0, 50) || 'File upload');
          if (!sessionId) {
            Alert.alert('Error', 'Failed to create session');
            setUploadingFiles(false);
            return;
          }
        }

        const uploadPromises = selectedFiles.map(file =>
          chatAPI.uploadAttachment(
            sessionId!,
            file.uri,
            file.name || 'file',
            file.type || 'application/octet-stream',
          ),
        );

        finalAttachmentIds = await Promise.all(uploadPromises);
        setSelectedFiles([]);
      } catch (err) {
        Alert.alert(
          'Upload Error',
          err instanceof Error ? err.message : 'Failed to upload files',
        );
        setUploadingFiles(false);
        return;
      } finally {
        setUploadingFiles(false);
      }
    }

    // Send message with attachment IDs
    await sendMessage(message, true, finalAttachmentIds);
  };

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

      <ChatInput
        onSend={handleSend}
        onFilesSelected={setSelectedFiles}
        selectedFiles={selectedFiles}
        isLoading={isLoading || uploadingFiles}
      />
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

