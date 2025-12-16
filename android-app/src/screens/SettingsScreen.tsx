import React, {useState} from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Switch,
  Alert,
  Platform,
} from 'react-native';
import Icon from 'react-native-vector-icons/Ionicons';
import {useAuth} from '../hooks/useAuth';
import {useTheme} from '../hooks/useTheme';
import {storage} from '../utils/storage';

export const SettingsScreen: React.FC = () => {
  const {user, logout} = useAuth();
  const {isDarkMode, toggleTheme} = useTheme();
  const [biometricEnabled, setBiometricEnabled] = useState(false);
  const [notificationsEnabled, setNotificationsEnabled] = useState(true);
  const [hapticEnabled, setHapticEnabled] = useState(true);

  const handleLogout = () => {
    Alert.alert('Sign Out', 'Are you sure you want to sign out?', [
      {text: 'Cancel', style: 'cancel'},
      {
        text: 'Sign Out',
        style: 'destructive',
        onPress: async () => {
          await logout();
        },
      },
    ]);
  };

  const handleBiometricToggle = async (value: boolean) => {
    if (value) {
      // In a real app, you would check biometric availability here
      Alert.alert(
        'Enable Biometric Login',
        'Use fingerprint or face recognition to sign in quickly?',
        [
          {text: 'Cancel', style: 'cancel'},
          {
            text: 'Enable',
            onPress: async () => {
              await storage.setBiometricEnabled(true);
              setBiometricEnabled(true);
            },
          },
        ],
      );
    } else {
      await storage.setBiometricEnabled(false);
      setBiometricEnabled(false);
    }
  };

  const handleClearCache = () => {
    Alert.alert(
      'Clear Cache',
      'This will remove all cached data. You will need to sign in again.',
      [
        {text: 'Cancel', style: 'cancel'},
        {
          text: 'Clear',
          style: 'destructive',
          onPress: async () => {
            await storage.clearCurrentSessionId();
            Alert.alert('Success', 'Cache cleared successfully');
          },
        },
      ],
    );
  };

  const SettingItem = ({
    icon,
    title,
    subtitle,
    onPress,
    rightElement,
    danger = false,
  }: {
    icon: string;
    title: string;
    subtitle?: string;
    onPress?: () => void;
    rightElement?: React.ReactNode;
    danger?: boolean;
  }) => (
    <TouchableOpacity
      style={[styles.settingItem, isDarkMode && styles.settingItemDark]}
      onPress={onPress}
      disabled={!onPress && !rightElement}>
      <View style={styles.settingItemLeft}>
        <View
          style={[
            styles.iconContainer,
            danger && styles.iconContainerDanger,
            isDarkMode && styles.iconContainerDark,
          ]}>
          <Icon
            name={icon}
            size={20}
            color={danger ? '#DC3545' : isDarkMode ? '#FFFFFF' : '#007AFF'}
          />
        </View>
        <View style={styles.settingTextContainer}>
          <Text
            style={[
              styles.settingTitle,
              danger && styles.settingTitleDanger,
              isDarkMode && styles.textLight,
            ]}>
            {title}
          </Text>
          {subtitle && (
            <Text style={[styles.settingSubtitle, isDarkMode && styles.textMuted]}>
              {subtitle}
            </Text>
          )}
        </View>
      </View>
      {rightElement || (onPress && <Icon name="chevron-forward" size={20} color="#999" />)}
    </TouchableOpacity>
  );

  return (
    <ScrollView
      style={[styles.container, isDarkMode && styles.containerDark]}
      contentContainerStyle={styles.content}>
      {/* Profile Section */}
      <View style={[styles.section, isDarkMode && styles.sectionDark]}>
        <View style={styles.profileHeader}>
          <View style={[styles.avatar, isDarkMode && styles.avatarDark]}>
            <Text style={styles.avatarText}>
              {user?.name?.charAt(0)?.toUpperCase() || user?.email?.charAt(0)?.toUpperCase() || 'U'}
            </Text>
          </View>
          <View style={styles.profileInfo}>
            <Text style={[styles.profileName, isDarkMode && styles.textLight]}>
              {user?.name || 'User'}
            </Text>
            <Text style={[styles.profileEmail, isDarkMode && styles.textMuted]}>
              {user?.email}
            </Text>
          </View>
        </View>
      </View>

      {/* Appearance Section */}
      <Text style={[styles.sectionTitle, isDarkMode && styles.textMuted]}>
        APPEARANCE
      </Text>
      <View style={[styles.section, isDarkMode && styles.sectionDark]}>
        <SettingItem
          icon="moon"
          title="Dark Mode"
          subtitle="Use dark theme across the app"
          rightElement={
            <Switch
              value={isDarkMode}
              onValueChange={toggleTheme}
              trackColor={{false: '#E9ECEF', true: '#007AFF'}}
              thumbColor={Platform.OS === 'android' ? '#FFFFFF' : undefined}
            />
          }
        />
      </View>

      {/* Security Section */}
      <Text style={[styles.sectionTitle, isDarkMode && styles.textMuted]}>
        SECURITY
      </Text>
      <View style={[styles.section, isDarkMode && styles.sectionDark]}>
        <SettingItem
          icon="finger-print"
          title="Biometric Login"
          subtitle="Use fingerprint or face ID to sign in"
          rightElement={
            <Switch
              value={biometricEnabled}
              onValueChange={handleBiometricToggle}
              trackColor={{false: '#E9ECEF', true: '#007AFF'}}
              thumbColor={Platform.OS === 'android' ? '#FFFFFF' : undefined}
            />
          }
        />
      </View>

      {/* Preferences Section */}
      <Text style={[styles.sectionTitle, isDarkMode && styles.textMuted]}>
        PREFERENCES
      </Text>
      <View style={[styles.section, isDarkMode && styles.sectionDark]}>
        <SettingItem
          icon="notifications"
          title="Push Notifications"
          subtitle="Receive news and update alerts"
          rightElement={
            <Switch
              value={notificationsEnabled}
              onValueChange={setNotificationsEnabled}
              trackColor={{false: '#E9ECEF', true: '#007AFF'}}
              thumbColor={Platform.OS === 'android' ? '#FFFFFF' : undefined}
            />
          }
        />
        <SettingItem
          icon="radio-button-on"
          title="Haptic Feedback"
          subtitle="Vibration on button presses"
          rightElement={
            <Switch
              value={hapticEnabled}
              onValueChange={setHapticEnabled}
              trackColor={{false: '#E9ECEF', true: '#007AFF'}}
              thumbColor={Platform.OS === 'android' ? '#FFFFFF' : undefined}
            />
          }
        />
      </View>

      {/* Data Section */}
      <Text style={[styles.sectionTitle, isDarkMode && styles.textMuted]}>
        DATA
      </Text>
      <View style={[styles.section, isDarkMode && styles.sectionDark]}>
        <SettingItem
          icon="trash-outline"
          title="Clear Cache"
          subtitle="Remove cached data and sessions"
          onPress={handleClearCache}
        />
      </View>

      {/* About Section */}
      <Text style={[styles.sectionTitle, isDarkMode && styles.textMuted]}>
        ABOUT
      </Text>
      <View style={[styles.section, isDarkMode && styles.sectionDark]}>
        <SettingItem icon="information-circle" title="Version" subtitle="1.0.0" />
        <SettingItem
          icon="document-text"
          title="Privacy Policy"
          onPress={() => Alert.alert('Privacy Policy', 'Coming soon')}
        />
        <SettingItem
          icon="shield-checkmark"
          title="Terms of Service"
          onPress={() => Alert.alert('Terms of Service', 'Coming soon')}
        />
      </View>

      {/* Sign Out */}
      <View style={[styles.section, isDarkMode && styles.sectionDark]}>
        <SettingItem
          icon="log-out-outline"
          title="Sign Out"
          onPress={handleLogout}
          danger
        />
      </View>

      <Text style={[styles.footer, isDarkMode && styles.textMuted]}>
        AmaniQuery v1.0.0{'\n'}Kenya's AI Legal Assistant
      </Text>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F8F9FA',
  },
  containerDark: {
    backgroundColor: '#121212',
  },
  content: {
    padding: 16,
  },
  section: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    marginBottom: 16,
    overflow: 'hidden',
  },
  sectionDark: {
    backgroundColor: '#1E1E1E',
  },
  sectionTitle: {
    fontSize: 13,
    fontWeight: '600',
    color: '#6C757D',
    marginBottom: 8,
    marginLeft: 4,
  },
  profileHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
  },
  avatar: {
    width: 60,
    height: 60,
    borderRadius: 30,
    backgroundColor: '#007AFF',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 16,
  },
  avatarDark: {
    backgroundColor: '#2563EB',
  },
  avatarText: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#FFFFFF',
  },
  profileInfo: {
    flex: 1,
  },
  profileName: {
    fontSize: 20,
    fontWeight: '600',
    color: '#212529',
    marginBottom: 4,
  },
  profileEmail: {
    fontSize: 14,
    color: '#6C757D',
  },
  settingItem: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#E9ECEF',
  },
  settingItemDark: {
    borderBottomColor: '#2D2D2D',
  },
  settingItemLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  iconContainer: {
    width: 36,
    height: 36,
    borderRadius: 8,
    backgroundColor: 'rgba(0, 122, 255, 0.1)',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  iconContainerDark: {
    backgroundColor: 'rgba(37, 99, 235, 0.2)',
  },
  iconContainerDanger: {
    backgroundColor: 'rgba(220, 53, 69, 0.1)',
  },
  settingTextContainer: {
    flex: 1,
  },
  settingTitle: {
    fontSize: 16,
    color: '#212529',
    marginBottom: 2,
  },
  settingTitleDanger: {
    color: '#DC3545',
  },
  settingSubtitle: {
    fontSize: 13,
    color: '#6C757D',
  },
  textLight: {
    color: '#FFFFFF',
  },
  textMuted: {
    color: '#9CA3AF',
  },
  footer: {
    textAlign: 'center',
    fontSize: 12,
    color: '#6C757D',
    marginTop: 8,
    marginBottom: 32,
    lineHeight: 18,
  },
});
