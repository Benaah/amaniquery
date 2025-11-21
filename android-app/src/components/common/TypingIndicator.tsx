import React, {useEffect} from 'react';
import {View, Text, StyleSheet} from 'react-native';
import Animated, {
  useAnimatedStyle,
  useSharedValue,
  withRepeat,
  withTiming,
  interpolate,
} from 'react-native-reanimated';

export const TypingIndicator: React.FC = () => {
  const dot1 = useSharedValue(0);
  const dot2 = useSharedValue(0);
  const dot3 = useSharedValue(0);

  useEffect(() => {
    dot1.value = withRepeat(withTiming(1, {duration: 400}), -1, true);
    dot2.value = withRepeat(withTiming(1, {duration: 400}), -1, true);
    dot3.value = withRepeat(withTiming(1, {duration: 400}), -1, true);
  }, [dot1, dot2, dot3]);

  const dot1Style = useAnimatedStyle(() => {
    return {
      opacity: interpolate(dot1.value, [0, 1], [0.3, 1]),
      transform: [
        {
          translateY: interpolate(dot1.value, [0, 1], [0, -8]),
        },
      ],
    };
  });

  const dot2Style = useAnimatedStyle(() => {
    return {
      opacity: interpolate(dot2.value, [0, 1], [0.3, 1]),
      transform: [
        {
          translateY: interpolate(dot2.value, [0, 1], [0, -8]),
        },
      ],
    };
  });

  const dot3Style = useAnimatedStyle(() => {
    return {
      opacity: interpolate(dot3.value, [0, 1], [0.3, 1]),
      transform: [
        {
          translateY: interpolate(dot3.value, [0, 1], [0, -8]),
        },
      ],
    };
  });

  return (
    <View style={styles.container}>
      <View style={styles.bubble}>
        <Animated.View style={[styles.dot, dot1Style]} />
        <Animated.View style={[styles.dot, dot2Style]} />
        <Animated.View style={[styles.dot, dot3Style]} />
      </View>
      <Text style={styles.text}>Thinking...</Text>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 12,
    gap: 12,
  },
  bubble: {
    flexDirection: 'row',
    backgroundColor: '#F8F9FA',
    borderRadius: 20,
    paddingHorizontal: 16,
    paddingVertical: 12,
    gap: 6,
    borderBottomLeftRadius: 4,
  },
  dot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: '#007AFF',
  },
  text: {
    fontSize: 14,
    color: '#666',
  },
});
