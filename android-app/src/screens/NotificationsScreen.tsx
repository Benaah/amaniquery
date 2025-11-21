import React from 'react';
import {View, StyleSheet} from 'react-native';
import {NotificationScreen as NotificationScreenComponent} from '../components/notifications/NotificationScreen';

export const NotificationsScreen: React.FC = () => {
  return (
    <View style={styles.container}>
      <NotificationScreenComponent />
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
});
