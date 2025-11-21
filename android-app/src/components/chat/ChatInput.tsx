import React, {useState, useRef} from 'react';
import {
  View,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
} from 'react-native';
import Icon from 'react-native-vector-icons/Ionicons';
import {FilePicker} from './FilePicker';
import {DocumentPickerResponse} from 'react-native-document-picker';

interface ChatInputProps {
  onSend: (message: string, attachmentIds?: string[]) => void;
  onFilesSelected?: (files: DocumentPickerResponse[]) => void;
  selectedFiles?: DocumentPickerResponse[];
  isLoading?: boolean;
  disabled?: boolean;
  placeholder?: string;
}

export const ChatInput: React.FC<ChatInputProps> = ({
  onSend,
  onFilesSelected,
  selectedFiles = [],
  isLoading = false,
  disabled = false,
  placeholder = 'Ask about Kenyan law, parliament, or news...',
}) => {
  const [input, setInput] = useState('');
  const [inputHeight, setInputHeight] = useState(44);
  const inputRef = useRef<TextInput>(null);

  const handleSend = () => {
    if ((input.trim() || selectedFiles.length > 0) && !isLoading && !disabled) {
      onSend(input.trim() || `Uploaded ${selectedFiles.length} file(s)`, []);
      setInput('');
      setInputHeight(44);
      onFilesSelected?.([]);
    }
  };

  const handleContentSizeChange = (event: any) => {
    const height = Math.min(
      Math.max(44, event.nativeEvent.contentSize.height + 20),
      200,
    );
    setInputHeight(height);
  };

  return (
    <View style={styles.container}>
      {selectedFiles.length > 0 && (
        <View style={styles.filePickerContainer}>
          <FilePicker
            files={selectedFiles}
            onFilesChange={onFilesSelected || (() => {})}
            maxFiles={5}
            maxSizeMB={10}
          />
        </View>
      )}
      <View style={styles.inputRow}>
        <TouchableOpacity
          style={styles.attachButton}
          onPress={() => {
            // File picker will be triggered by FilePicker component
          }}
          disabled={isLoading || disabled}
          activeOpacity={0.7}>
          <Icon name="attach" size={22} color="#007AFF" />
        </TouchableOpacity>
        <View style={styles.inputWrapper}>
          <TextInput
            ref={inputRef}
            style={[styles.input, {height: inputHeight}]}
            value={input}
            onChangeText={setInput}
            onContentSizeChange={handleContentSizeChange}
            placeholder={placeholder}
            placeholderTextColor="#999"
            multiline
            maxLength={1000}
            editable={!isLoading && !disabled}
            textAlignVertical="center"
            blurOnSubmit={false}
          />
        </View>
        <TouchableOpacity
          style={[
            styles.sendButton,
            (isLoading || disabled || !input.trim()) &&
              styles.sendButtonDisabled,
          ]}
          onPress={handleSend}
          disabled={isLoading || disabled || !input.trim()}
          activeOpacity={0.8}>
          {isLoading ? (
            <ActivityIndicator size="small" color="#FFFFFF" />
          ) : (
            <Icon name="send" size={20} color="#FFFFFF" />
          )}
        </TouchableOpacity>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    padding: 12,
    backgroundColor: '#FFFFFF',
    borderTopWidth: 1,
    borderTopColor: '#E9ECEF',
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: -2,
    },
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 5,
  },
  filePickerContainer: {
    marginBottom: 8,
  },
  inputRow: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    gap: 8,
  },
  attachButton: {
    width: 44,
    height: 44,
    borderRadius: 22,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#F8F9FA',
  },
  inputWrapper: {
    flex: 1,
    borderRadius: 22,
    backgroundColor: '#F8F9FA',
    borderWidth: 1,
    borderColor: '#E9ECEF',
    overflow: 'hidden',
  },
  input: {
    flex: 1,
    fontSize: 16,
    paddingHorizontal: 16,
    paddingVertical: 12,
    minHeight: 44,
    maxHeight: 200,
    color: '#000',
  },
  sendButton: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: '#007AFF',
    justifyContent: 'center',
    alignItems: 'center',
  },
  sendButtonDisabled: {
    backgroundColor: '#DEE2E6',
  },
});
