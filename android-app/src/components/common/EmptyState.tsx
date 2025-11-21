import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
} from 'react-native';
import Icon from 'react-native-vector-icons/Ionicons';
import {useChat} from '../../hooks/useChat';

interface EmptyStateProps {
  isResearchMode?: boolean;
  useHybrid?: boolean;
}

interface SuggestionTile {
  title: string;
  description: string;
}

const suggestedQuestions: SuggestionTile[] = [
  {
    title: 'Latest developments in Kenyan constitutional law',
    description: 'Get a rapid scan of amendments, rulings, and reforms.',
  },
  {
    title: 'Recent changes to the Kenyan Penal Code',
    description: 'Understand how new provisions impact compliance.',
  },
  {
    title: 'Key provisions of the Competition Act',
    description: 'Summaries on enforcement thresholds and penalties.',
  },
  {
    title: 'Environmental law cases in Kenyan courts',
    description: 'Explore how judges interpret conservation mandates.',
  },
  {
    title: 'Requirements for starting a business in Kenya',
    description: 'Licensing, compliance, and registration checklist.',
  },
];

const researchSuggestedQuestions: SuggestionTile[] = [
  {
    title: 'Comprehensive analysis of the Bill of Rights',
    description: 'Focus on digital rights and emerging jurisprudence.',
  },
  {
    title: 'Evolution of environmental law in Kenya',
    description: 'Trace policy effectiveness against conservation goals.',
  },
  {
    title: 'Impact of Penal Code amendments on cybercrime',
    description: 'Deep dive into enforcement trends and loopholes.',
  },
  {
    title: 'Devolution framework in the Constitution',
    description: 'Assess implementation challenges across counties.',
  },
  {
    title: 'Data protection and privacy rights landscape',
    description: 'Map compliance expectations to ICT deployments.',
  },
];

export const EmptyState: React.FC<EmptyStateProps> = ({
  isResearchMode = false,
  useHybrid = false,
}) => {
  const {sendMessage} = useChat();

  const questions = isResearchMode
    ? researchSuggestedQuestions
    : suggestedQuestions;

  return (
    <ScrollView
      contentContainerStyle={styles.container}
      showsVerticalScrollIndicator={false}>
      <View style={styles.content}>
        <View style={styles.iconContainer}>
          <Icon name="chatbubbles" size={48} color="#007AFF" />
        </View>

        <Text style={styles.title}>Welcome to AmaniQuery</Text>

        {(isResearchMode || useHybrid) && (
          <View style={styles.badgeContainer}>
            {isResearchMode && (
              <View style={[styles.badge, styles.researchBadge]}>
                <Icon name="search" size={14} color="#FFFFFF" />
                <Text style={styles.badgeText}>Research Mode</Text>
              </View>
            )}
            {useHybrid && !isResearchMode && (
              <View style={[styles.badge, styles.hybridBadge]}>
                <Icon name="sparkles" size={14} color="#FFFFFF" />
                <Text style={styles.badgeText}>Hybrid Mode</Text>
              </View>
            )}
          </View>
        )}

        <Text style={styles.description}>
          {isResearchMode
            ? 'Submit a detailed Kenyan legal question and receive structured analysis built for citations and downstream reporting.'
            : useHybrid
            ? 'Enhanced RAG with hybrid encoder and adaptive retrieval. Ask about Kenyan law, parliament, or current affairs with improved accuracy.'
            : 'Ask about Kenyan law, parliament, or current affairs. Answers stream in real time with sources you can trust.'}
        </Text>

        <View style={styles.suggestionsContainer}>
          {questions.map((question, index) => (
            <TouchableOpacity
              key={index}
              style={styles.suggestionCard}
              onPress={() => sendMessage(question.title, true, undefined)}
              activeOpacity={0.7}>
              <View style={styles.suggestionIcon}>
                <Icon name="sparkles" size={20} color="#007AFF" />
              </View>
              <View style={styles.suggestionContent}>
                <Text style={styles.suggestionTitle}>{question.title}</Text>
                <Text style={styles.suggestionDescription}>
                  {question.description}
                </Text>
              </View>
              <Icon
                name="arrow-up-right"
                size={16}
                color="#999"
                style={styles.suggestionArrow}
              />
            </TouchableOpacity>
          ))}
        </View>
      </View>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flexGrow: 1,
    justifyContent: 'center',
    padding: 20,
  },
  content: {
    alignItems: 'center',
  },
  iconContainer: {
    width: 80,
    height: 80,
    borderRadius: 24,
    backgroundColor: 'rgba(0, 122, 255, 0.1)',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 24,
    borderWidth: 1,
    borderColor: 'rgba(0, 122, 255, 0.2)',
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#000',
    marginBottom: 12,
    textAlign: 'center',
  },
  badgeContainer: {
    flexDirection: 'row',
    gap: 8,
    marginBottom: 16,
  },
  badge: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
    gap: 6,
  },
  researchBadge: {
    backgroundColor: '#0066CC',
  },
  hybridBadge: {
    backgroundColor: '#6B46C1',
  },
  badgeText: {
    color: '#FFFFFF',
    fontSize: 12,
    fontWeight: '600',
  },
  description: {
    fontSize: 16,
    color: '#666',
    textAlign: 'center',
    marginBottom: 32,
    lineHeight: 24,
    paddingHorizontal: 16,
  },
  suggestionsContainer: {
    width: '100%',
    gap: 12,
  },
  suggestionCard: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    backgroundColor: '#F8F9FA',
    borderRadius: 16,
    padding: 16,
    borderWidth: 1,
    borderColor: '#E9ECEF',
    gap: 12,
  },
  suggestionIcon: {
    width: 40,
    height: 40,
    borderRadius: 12,
    backgroundColor: 'rgba(0, 122, 255, 0.15)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  suggestionContent: {
    flex: 1,
  },
  suggestionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#000',
    marginBottom: 4,
    lineHeight: 22,
  },
  suggestionDescription: {
    fontSize: 14,
    color: '#666',
    lineHeight: 20,
  },
  suggestionArrow: {
    marginTop: 4,
  },
});
