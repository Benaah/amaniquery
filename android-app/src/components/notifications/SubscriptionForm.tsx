import React, {useState, useEffect} from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  ScrollView,
  Alert,
} from 'react-native';
import {notificationsAPI} from '../../api/notifications';
import {NotificationSource} from '../../types';
import {LoadingSpinner} from '../common/LoadingSpinner';
import {ErrorMessage} from '../common/ErrorMessage';

interface SubscriptionFormProps {
  onSubmit: () => void;
}

export const SubscriptionForm: React.FC<SubscriptionFormProps> = ({onSubmit}) => {
  const [phoneNumber, setPhoneNumber] = useState('');
  const [deliveryMethod, setDeliveryMethod] = useState<'sms' | 'whatsapp'>('whatsapp');
  const [selectedCategories, setSelectedCategories] = useState<string[]>([]);
  const [selectedSources, setSelectedSources] = useState<string[]>([]);
  const [sources, setSources] = useState<NotificationSource[]>([]);
  const [categories] = useState<string[]>([
    'Kenyan Law',
    'Parliament',
    'Kenyan News',
    'Global Trend',
  ]);
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    loadSources();
  }, []);

  const loadSources = async () => {
    setLoading(true);
    try {
      const data = await notificationsAPI.getSources();
      setSources(data);
    } catch (err) {
      setError('Failed to load sources');
    } finally {
      setLoading(false);
    }
  };

  const toggleCategory = (category: string) => {
    setSelectedCategories(prev =>
      prev.includes(category)
        ? prev.filter(c => c !== category)
        : [...prev, category],
    );
  };

  const toggleSource = (sourceName: string) => {
    setSelectedSources(prev =>
      prev.includes(sourceName)
        ? prev.filter(s => s !== sourceName)
        : [...prev, sourceName],
    );
  };

  const handleSubmit = async () => {
    if (!phoneNumber.trim()) {
      Alert.alert('Error', 'Please enter a phone number');
      return;
    }

    setSubmitting(true);
    setError(null);
    setSuccess(null);

    try {
      await notificationsAPI.createSubscription({
        phone_number: phoneNumber.trim(),
        delivery_method: deliveryMethod,
        categories: selectedCategories.length > 0 ? selectedCategories : categories,
        sources: selectedSources.length > 0 ? selectedSources : sources.map(s => s.name),
      });

      setSuccess('Successfully subscribed to notifications!');
      setTimeout(() => {
        onSubmit();
      }, 2000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to subscribe');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <Text style={styles.title}>Subscribe to News Notifications</Text>
      <Text style={styles.description}>
        Get instant updates about Kenyan legal news, parliamentary proceedings, and more
        via SMS or WhatsApp.
      </Text>

      {error && <ErrorMessage message={error} />}
      {success && (
        <View style={styles.successContainer}>
          <Text style={styles.successText}>{success}</Text>
        </View>
      )}

      <View style={styles.section}>
        <Text style={styles.label}>Phone Number</Text>
        <TextInput
          style={styles.input}
          value={phoneNumber}
          onChangeText={setPhoneNumber}
          placeholder="e.g., 0712345678 or +254712345678"
          keyboardType="phone-pad"
          editable={!submitting}
        />
      </View>

      <View style={styles.section}>
        <Text style={styles.label}>Delivery Method</Text>
        <View style={styles.buttonRow}>
          <TouchableOpacity
            style={[
              styles.methodButton,
              deliveryMethod === 'whatsapp' && styles.methodButtonActive,
            ]}
            onPress={() => setDeliveryMethod('whatsapp')}
            disabled={submitting}>
            <Text
              style={[
                styles.methodButtonText,
                deliveryMethod === 'whatsapp' && styles.methodButtonTextActive,
              ]}>
              WhatsApp
            </Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[
              styles.methodButton,
              deliveryMethod === 'sms' && styles.methodButtonActive,
            ]}
            onPress={() => setDeliveryMethod('sms')}
            disabled={submitting}>
            <Text
              style={[
                styles.methodButtonText,
                deliveryMethod === 'sms' && styles.methodButtonTextActive,
              ]}>
              SMS
            </Text>
          </TouchableOpacity>
        </View>
      </View>

      <View style={styles.section}>
        <Text style={styles.label}>
          Categories (Optional - leave empty for all)
        </Text>
        <View style={styles.chipContainer}>
          {categories.map(category => (
            <TouchableOpacity
              key={category}
              style={[
                styles.chip,
                selectedCategories.includes(category) && styles.chipActive,
              ]}
              onPress={() => toggleCategory(category)}
              disabled={submitting}>
              <Text
                style={[
                  styles.chipText,
                  selectedCategories.includes(category) && styles.chipTextActive,
                ]}>
                {category}
              </Text>
            </TouchableOpacity>
          ))}
        </View>
      </View>

      <View style={styles.section}>
        <Text style={styles.label}>Sources (Optional - leave empty for all)</Text>
        {loading ? (
          <LoadingSpinner />
        ) : (
          <View style={styles.chipContainer}>
            {sources.map(source => (
              <TouchableOpacity
                key={source.name}
                style={[
                  styles.chip,
                  selectedSources.includes(source.name) && styles.chipActive,
                ]}
                onPress={() => toggleSource(source.name)}
                disabled={submitting}>
                <Text
                  style={[
                    styles.chipText,
                    selectedSources.includes(source.name) && styles.chipTextActive,
                  ]}>
                  {source.name} ({source.article_count})
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        )}
      </View>

      <TouchableOpacity
        style={[styles.submitButton, submitting && styles.submitButtonDisabled]}
        onPress={handleSubmit}
        disabled={submitting}>
        <Text style={styles.submitButtonText}>
          {submitting ? 'Subscribing...' : 'Subscribe'}
        </Text>
      </TouchableOpacity>
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
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#212529',
    marginBottom: 8,
  },
  description: {
    fontSize: 14,
    color: '#6C757D',
    marginBottom: 24,
    lineHeight: 20,
  },
  section: {
    marginBottom: 24,
  },
  label: {
    fontSize: 16,
    fontWeight: '600',
    color: '#212529',
    marginBottom: 8,
  },
  input: {
    borderWidth: 1,
    borderColor: '#DEE2E6',
    borderRadius: 8,
    padding: 12,
    fontSize: 16,
    backgroundColor: '#FFFFFF',
  },
  buttonRow: {
    flexDirection: 'row',
    gap: 12,
  },
  methodButton: {
    flex: 1,
    padding: 12,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#DEE2E6',
    alignItems: 'center',
    backgroundColor: '#FFFFFF',
  },
  methodButtonActive: {
    backgroundColor: '#007AFF',
    borderColor: '#007AFF',
  },
  methodButtonText: {
    fontSize: 16,
    color: '#212529',
  },
  methodButtonTextActive: {
    color: '#FFFFFF',
    fontWeight: '600',
  },
  chipContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  chip: {
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: '#DEE2E6',
    backgroundColor: '#FFFFFF',
  },
  chipActive: {
    backgroundColor: '#007AFF',
    borderColor: '#007AFF',
  },
  chipText: {
    fontSize: 14,
    color: '#212529',
  },
  chipTextActive: {
    color: '#FFFFFF',
    fontWeight: '600',
  },
  submitButton: {
    backgroundColor: '#007AFF',
    borderRadius: 8,
    padding: 16,
    alignItems: 'center',
    marginTop: 8,
  },
  submitButtonDisabled: {
    backgroundColor: '#DEE2E6',
  },
  submitButtonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '600',
  },
  successContainer: {
    backgroundColor: '#D4EDDA',
    borderColor: '#28A745',
    borderWidth: 1,
    borderRadius: 8,
    padding: 12,
    marginBottom: 16,
  },
  successText: {
    color: '#155724',
    fontSize: 14,
  },
});

