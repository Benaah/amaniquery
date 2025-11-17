import React, {useState} from 'react';
import {
  View,
  Text,
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
}

export const ChatInput: React.FC<ChatInputProps> = ({
  onSend,
  onFilesSelected,
  selectedFiles = [],
  isLoading = false,
  disabled = false,
}) => {
  const [input, setInput] = useState('');

  const handleSend = () => {
    if ((input.trim() || selectedFiles.length > 0) && !isLoading && !disabled) {
      onSend(input.trim() || `Uploaded ${selectedFiles.length} file(s)`, []);
      setInput('');
      onFilesSelected?.([]);
    }
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
          disabled={isLoading || disabled}>
          <Icon name="attach" size={20} color="#007AFF" />
        </TouchableOpacity>
        <TextInput
        style={styles.input}
        value={input}
        onChangeText={setInput}
        placeholder="Ask about Kenyan law, parliament, or news..."
        placeholderTextColor="#999"
        multiline
        maxLength={1000}
        editable={!isLoading && !disabled}
        onSubmitEditing={handleSend}
      />
      </View>
      <TouchableOpacity
        style={[
          styles.sendButton,
          (isLoading || disabled || !input.trim()) && styles.sendButtonDisabled,
        ]}
        onPress={handleSend}
        disabled={isLoading || disabled || !input.trim()}>
        {isLoading ? (
          <ActivityIndicator size="small" color="#FFFFFF" />
        ) : (
          <Text style={styles.sendButtonText}>Send</Text>
        )}
      </TouchableOpacity>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    padding: 12,
    backgroundColor: '#FFFFFF',
    borderTopWidth: 1,
    borderTopColor: '#E9ECEF',
  },
  filePickerContainer: {
    marginBottom: 8,
  },
  inputRow: {
    flexDirection: 'row',
    alignItems: 'flex-end',
  },
  attachButton: {
    padding: 8,
    marginRight: 8,
  },
  input: {
    flex: 1,
    borderWidth: 1,
    borderColor: '#DEE2E6',
    borderRadius: 20,
    paddingHorizontal: 16,
    paddingVertical: 10,
    maxHeight: 100,
    fontSize: 16,
    marginRight: 8,
    flex: 1,
  },
  sendButton: {
    backgroundColor: '#007AFF',
    borderRadius: 20,
    paddingHorizontal: 20,
    paddingVertical: 10,
    justifyContent: 'center',
    alignItems: 'center',
    minWidth: 70,
  },
  sendButtonDisabled: {
    backgroundColor: '#DEE2E6',
  },
  sendButtonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '600',
  },
});

