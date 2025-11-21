import React from 'react';
import Icon from 'react-native-vector-icons/Ionicons';
import {NavigationContainer} from '@react-navigation/native';
import {createBottomTabNavigator} from '@react-navigation/bottom-tabs';
import {createStackNavigator} from '@react-navigation/stack';
import {useAuth} from '../hooks/useAuth';
import {ActivityIndicator, View, StyleSheet} from 'react-native';
import {HomeScreen} from '../screens/HomeScreen';
import {ChatScreen} from '../screens/ChatScreen';
import {VoiceScreen} from '../screens/VoiceScreen';
import {NotificationsScreen} from '../screens/NotificationsScreen';
import {SignInScreen} from '../screens/auth/SignInScreen';
import {SignUpScreen} from '../screens/auth/SignUpScreen';
import {ForgotPasswordScreen} from '../screens/auth/ForgotPasswordScreen';

const Tab = createBottomTabNavigator();
const Stack = createStackNavigator();
const AuthStack = createStackNavigator();

const MainTabs = () => {
  return (
    <Tab.Navigator
      screenOptions={{
        headerShown: false,
        tabBarActiveTintColor: '#007AFF',
        tabBarInactiveTintColor: '#6C757D',
        tabBarStyle: {
          backgroundColor: '#FFFFFF',
          borderTopWidth: 1,
          borderTopColor: '#E9ECEF',
        },
      }}>
      <Tab.Screen
        name="Home"
        component={HomeScreen}
        options={{
          tabBarLabel: 'Home',
          tabBarIcon: ({color, size}) => (
            <Icon name="home" size={size || 24} color={color} />
          ),
        }}
      />
      <Tab.Screen
        name="Chat"
        component={ChatScreen}
        options={{
          tabBarLabel: 'Chat',
          tabBarIcon: ({color, size}) => (
            <Icon name="chatbubbles" size={size || 24} color={color} />
          ),
        }}
      />
      <Tab.Screen
        name="Voice"
        component={VoiceScreen}
        options={{
          tabBarLabel: 'Voice',
          tabBarIcon: ({color, size}) => (
            <Icon name="mic" size={size || 24} color={color} />
          ),
        }}
      />
      <Tab.Screen
        name="Notifications"
        component={NotificationsScreen}
        options={{
          tabBarLabel: 'Notifications',
          tabBarIcon: ({color, size}) => (
            <Icon name="notifications" size={size || 24} color={color} />
          ),
        }}
      />
    </Tab.Navigator>
  );
};

const AuthNavigator = () => {
  return (
    <AuthStack.Navigator screenOptions={{headerShown: false}}>
      <AuthStack.Screen name="SignIn" component={SignInScreen} />
      <AuthStack.Screen name="SignUp" component={SignUpScreen} />
      <AuthStack.Screen
        name="ForgotPassword"
        component={ForgotPasswordScreen}
      />
    </AuthStack.Navigator>
  );
};

export const AppNavigator: React.FC = () => {
  const {isAuthenticated, loading} = useAuth();

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#007AFF" />
      </View>
    );
  }

  return (
    <NavigationContainer>
      <Stack.Navigator screenOptions={{headerShown: false}}>
        {isAuthenticated ? (
          <Stack.Screen name="Main" component={MainTabs} />
        ) : (
          <Stack.Screen name="Auth" component={AuthNavigator} />
        )}
      </Stack.Navigator>
    </NavigationContainer>
  );
};

const styles = StyleSheet.create({
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#FFFFFF',
  },
});
