import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
} from 'react-native';
import Icon from 'react-native-vector-icons/Ionicons';
import {useNavigation} from '@react-navigation/native';

export const HomeScreen: React.FC = () => {
  const navigation = useNavigation<any>();

  const features = [
    {
      id: 'chat',
      title: 'Chat',
      description: 'Query the legal knowledge base with AI-powered responses',
      icon: 'chatbubbles',
      route: 'Chat',
      color: '#007AFF',
    },
    {
      id: 'voice',
      title: 'Voice Agent',
      description: 'Real-time voice conversations with the AI assistant',
      icon: 'mic',
      route: 'Voice',
      color: '#28A745',
    },
    {
      id: 'notifications',
      title: 'Notifications',
      description: 'Subscribe to news updates via SMS or WhatsApp',
      icon: 'notifications',
      route: 'Notifications',
      color: '#FFC107',
    },
  ];

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <View style={styles.header}>
        <Text style={styles.title}>AmaniQuery</Text>
        <Text style={styles.subtitle}>Kenya's AI Legal Assistant</Text>
      </View>

      <Text style={styles.description}>
        Experience the future of legal research with AmaniQuery - an intelligent
        RAG system that combines constitutional law, parliamentary proceedings,
        and news analysis to provide accurate, verifiable answers about Kenyan
        governance.
      </Text>

      <View style={styles.featuresContainer}>
        {features.map(feature => (
          <TouchableOpacity
            key={feature.id}
            style={[styles.featureCard, {borderLeftColor: feature.color}]}
            onPress={() => navigation.navigate(feature.route)}>
            <View style={styles.featureHeader}>
              <Icon
                name={feature.icon}
                size={24}
                color={feature.color}
                style={styles.featureIcon}
              />
              <Text style={styles.featureTitle}>{feature.title}</Text>
            </View>
            <Text style={styles.featureDescription}>{feature.description}</Text>
          </TouchableOpacity>
        ))}
      </View>

      <View style={styles.infoCard}>
        <Text style={styles.infoTitle}>About AmaniQuery</Text>
        <Text style={styles.infoText}>
          AmaniQuery democratizes access to Kenyan legal information through
          AI-powered intelligence. Get instant answers about constitutional law,
          parliamentary proceedings, and legal news.
        </Text>
      </View>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#FFFFFF',
  },
  content: {
    padding: 16,
  },
  header: {
    marginBottom: 24,
    alignItems: 'center',
  },
  title: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#212529',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 18,
    color: '#6C757D',
  },
  description: {
    fontSize: 14,
    color: '#495057',
    lineHeight: 22,
    marginBottom: 32,
    textAlign: 'center',
  },
  featuresContainer: {
    gap: 16,
    marginBottom: 32,
  },
  featureCard: {
    backgroundColor: '#F8F9FA',
    borderRadius: 12,
    padding: 20,
    borderLeftWidth: 4,
    borderWidth: 1,
    borderColor: '#E9ECEF',
  },
  featureHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  featureIcon: {
    marginRight: 12,
  },
  featureTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: '#212529',
  },
  featureDescription: {
    fontSize: 14,
    color: '#6C757D',
    lineHeight: 20,
  },
  infoCard: {
    backgroundColor: '#E3F2FD',
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    borderColor: '#BBDEFB',
  },
  infoTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1976D2',
    marginBottom: 8,
  },
  infoText: {
    fontSize: 14,
    color: '#424242',
    lineHeight: 20,
  },
});

