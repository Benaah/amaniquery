import React, {useState, useEffect, useRef} from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  TextInput,
  Alert,
} from 'react-native';
import {Room, RoomEvent, RemoteParticipant, DataPacket_Kind} from '@livekit/react-native';
import {voiceAPI} from '../../api/voice';
import {LIVEKIT_URL} from '../../utils/config';
import {TranscriptView, TranscriptMessage} from './TranscriptView';
import {VoiceControls} from './VoiceControls';
import {LoadingSpinner} from '../common/LoadingSpinner';
import {ErrorMessage} from '../common/ErrorMessage';

export const VoiceScreen: React.FC = () => {
  const [room, setRoom] = useState<Room | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [messages, setMessages] = useState<TranscriptMessage[]>([]);
  const [roomName, setRoomName] = useState(`voice-${Date.now()}`);
  const [currentUserTranscript, setCurrentUserTranscript] = useState('');
  const [currentAgentTranscript, setCurrentAgentTranscript] = useState('');
  const roomRef = useRef<Room | null>(null);

  useEffect(() => {
    return () => {
      if (roomRef.current) {
        roomRef.current.disconnect();
      }
    };
  }, []);

  const connectToRoom = async () => {
    if (!LIVEKIT_URL) {
      setError('LiveKit URL is not configured');
      return;
    }

    setIsConnecting(true);
    setError(null);

    try {
      // Generate token from backend
      const token = await voiceAPI.generateToken(roomName, 'user');

      // Create and connect to room
      const newRoom = new Room();
      roomRef.current = newRoom;

      // Set up event listeners
      newRoom.on(RoomEvent.Connected, () => {
        setIsConnected(true);
        setIsConnecting(false);
        setRoom(newRoom);
      });

      newRoom.on(RoomEvent.Disconnected, () => {
        setIsConnected(false);
        setRoom(null);
        roomRef.current = null;
      });

      newRoom.on(RoomEvent.DataReceived, (payload, participant) => {
        if (participant && participant !== newRoom.localParticipant) {
          try {
            const data = JSON.parse(new TextDecoder().decode(payload));
            if (data.type === 'transcript' && data.role === 'assistant') {
              if (data.is_final) {
                const message: TranscriptMessage = {
                  id: `agent-${Date.now()}`,
                  role: 'assistant',
                  content: data.text,
                  timestamp: new Date(),
                };
                setMessages(prev => [...prev, message]);
                setCurrentAgentTranscript('');
              } else {
                setCurrentAgentTranscript(data.text);
              }
            }
          } catch (e) {
            console.error('Failed to parse transcript data:', e);
          }
        }
      });

      // Connect to room
      await newRoom.connect(LIVEKIT_URL, token);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to connect');
      setIsConnecting(false);
    }
  };

  const disconnect = async () => {
    if (roomRef.current) {
      await roomRef.current.disconnect();
      setRoom(null);
      roomRef.current = null;
      setIsConnected(false);
      setMessages([]);
    }
  };

  const toggleMute = async () => {
    if (!room) return;

    try {
      const micEnabled = room.localParticipant?.isMicrophoneEnabled ?? false;
      await room.localParticipant?.setMicrophoneEnabled(!micEnabled);
      setIsMuted(!micEnabled);
    } catch (err) {
      Alert.alert('Error', 'Failed to toggle microphone');
    }
  };

  if (isConnected && room) {
    return (
      <View style={styles.container}>
        <View style={styles.header}>
          <Text style={styles.title}>Voice Session</Text>
          <Text style={styles.roomName}>Room: {roomName}</Text>
        </View>

        <TranscriptView
          messages={[
            ...messages,
            ...(currentUserTranscript
              ? [
                  {
                    id: 'user-streaming',
                    role: 'user' as const,
                    content: currentUserTranscript,
                    timestamp: new Date(),
                    isStreaming: true,
                  },
                ]
              : []),
            ...(currentAgentTranscript
              ? [
                  {
                    id: 'agent-streaming',
                    role: 'assistant' as const,
                    content: currentAgentTranscript,
                    timestamp: new Date(),
                    isStreaming: true,
                  },
                ]
              : []),
          ]}
        />

        <VoiceControls
          isConnected={isConnected}
          isMuted={isMuted}
          onToggleMute={toggleMute}
          onDisconnect={disconnect}
        />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <View style={styles.connectContainer}>
        <Text style={styles.title}>Start Voice Session</Text>

        <TextInput
          style={styles.input}
          value={roomName}
          onChangeText={setRoomName}
          placeholder="Room name"
          editable={!isConnecting}
        />

        {error && <ErrorMessage message={error} />}

        {isConnecting ? (
          <LoadingSpinner />
        ) : (
          <TouchableOpacity
            style={styles.connectButton}
            onPress={connectToRoom}
            disabled={!roomName.trim()}>
            <Text style={styles.connectButtonText}>Connect</Text>
          </TouchableOpacity>
        )}
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#FFFFFF',
  },
  header: {
    padding: 16,
    backgroundColor: '#F8F9FA',
    borderBottomWidth: 1,
    borderBottomColor: '#E9ECEF',
  },
  title: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#212529',
    marginBottom: 4,
  },
  roomName: {
    fontSize: 14,
    color: '#6C757D',
  },
  connectContainer: {
    flex: 1,
    justifyContent: 'center',
    padding: 24,
  },
  input: {
    borderWidth: 1,
    borderColor: '#DEE2E6',
    borderRadius: 8,
    padding: 12,
    fontSize: 16,
    marginBottom: 16,
  },
  connectButton: {
    backgroundColor: '#007AFF',
    borderRadius: 8,
    padding: 16,
    alignItems: 'center',
  },
  connectButtonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '600',
  },
});

