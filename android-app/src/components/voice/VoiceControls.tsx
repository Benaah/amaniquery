import React from 'react';
import {View, TouchableOpacity, Text, StyleSheet} from 'react-native';

interface VoiceControlsProps {
  isConnected: boolean;
  isMuted: boolean;
  onToggleMute: () => void;
  onDisconnect: () => void;
}

export const VoiceControls: React.FC<VoiceControlsProps> = ({
  isConnected,
  isMuted,
  onToggleMute,
  onDisconnect,
}) => {
  return (
    <View style={styles.container}>
      <TouchableOpacity
        style={[styles.button, isMuted ? styles.mutedButton : styles.unmutedButton]}
        onPress={onToggleMute}
        disabled={!isConnected}>
        <Text style={styles.buttonText}>{isMuted ? '🔇 Unmute' : '🎤 Mute'}</Text>
      </TouchableOpacity>

      <TouchableOpacity
        style={[styles.button, styles.disconnectButton]}
        onPress={onDisconnect}
        disabled={!isConnected}>
        <Text style={styles.buttonText}>Disconnect</Text>
      </TouchableOpacity>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    padding: 16,
    backgroundColor: '#FFFFFF',
    borderTopWidth: 1,
    borderTopColor: '#E9ECEF',
  },
  button: {
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 24,
    minWidth: 120,
    alignItems: 'center',
  },
  unmutedButton: {
    backgroundColor: '#28A745',
  },
  mutedButton: {
    backgroundColor: '#DC3545',
  },
  disconnectButton: {
    backgroundColor: '#6C757D',
  },
  buttonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '600',
  },
});

