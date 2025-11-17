import React, {useState, useEffect} from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  RefreshControl,
} from 'react-native';
import {notificationsAPI} from '../../api/notifications';
import {SubscriptionForm} from './SubscriptionForm';
import {LoadingSpinner} from '../common/LoadingSpinner';
import {ErrorMessage} from '../common/ErrorMessage';

export const NotificationScreen: React.FC = () => {
  const [showForm, setShowForm] = useState(false);
  const [subscriptions, setSubscriptions] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    if (!showForm) {
      loadSubscriptions();
    }
  }, [showForm]);

  const loadSubscriptions = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await notificationsAPI.getSubscriptions();
      setSubscriptions(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load subscriptions');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const handleRefresh = () => {
    setRefreshing(true);
    loadSubscriptions();
  };

  const handleDelete = async (id: string) => {
    try {
      await notificationsAPI.deleteSubscription(id);
      await loadSubscriptions();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete subscription');
    }
  };

  if (showForm) {
    return (
      <View style={styles.container}>
        <View style={styles.header}>
          <TouchableOpacity onPress={() => setShowForm(false)}>
            <Text style={styles.backButton}>← Back</Text>
          </TouchableOpacity>
          <Text style={styles.headerTitle}>New Subscription</Text>
        </View>
        <SubscriptionForm onSubmit={() => setShowForm(false)} />
      </View>
    );
  }

  return (
    <ScrollView
      style={styles.container}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={handleRefresh} />
      }>
      <View style={styles.content}>
        <Text style={styles.title}>News Notifications</Text>
        <Text style={styles.description}>
          Subscribe to receive updates about Kenyan legal news, parliamentary
          proceedings, and more via SMS or WhatsApp.
        </Text>

        {error && <ErrorMessage message={error} />}

        <TouchableOpacity
          style={styles.addButton}
          onPress={() => setShowForm(true)}>
          <Text style={styles.addButtonText}>+ New Subscription</Text>
        </TouchableOpacity>

        {loading ? (
          <LoadingSpinner />
        ) : subscriptions.length === 0 ? (
          <View style={styles.emptyContainer}>
            <Text style={styles.emptyText}>No subscriptions yet</Text>
            <Text style={styles.emptySubtext}>
              Create a subscription to start receiving notifications
            </Text>
          </View>
        ) : (
          <View style={styles.subscriptionsList}>
            {subscriptions.map(subscription => (
              <View key={subscription.id} style={styles.subscriptionCard}>
                <View style={styles.subscriptionHeader}>
                  <Text style={styles.subscriptionPhone}>
                    {subscription.phone_number}
                  </Text>
                  <View
                    style={[
                      styles.statusBadge,
                      subscription.active
                        ? styles.statusBadgeActive
                        : styles.statusBadgeInactive,
                    ]}>
                    <Text style={styles.statusText}>
                      {subscription.active ? 'Active' : 'Inactive'}
                    </Text>
                  </View>
                </View>
                <Text style={styles.subscriptionMethod}>
                  Delivery: {subscription.delivery_method.toUpperCase()}
                </Text>
                {subscription.categories && subscription.categories.length > 0 && (
                  <Text style={styles.subscriptionInfo}>
                    Categories: {subscription.categories.join(', ')}
                  </Text>
                )}
                {subscription.sources && subscription.sources.length > 0 && (
                  <Text style={styles.subscriptionInfo}>
                    Sources: {subscription.sources.length} selected
                  </Text>
                )}
                <TouchableOpacity
                  style={styles.deleteButton}
                  onPress={() => handleDelete(subscription.id)}>
                  <Text style={styles.deleteButtonText}>Delete</Text>
                </TouchableOpacity>
              </View>
            ))}
          </View>
        )}
      </View>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#FFFFFF',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#E9ECEF',
  },
  backButton: {
    fontSize: 16,
    color: '#007AFF',
    marginRight: 16,
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#212529',
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
  addButton: {
    backgroundColor: '#007AFF',
    borderRadius: 8,
    padding: 16,
    alignItems: 'center',
    marginBottom: 24,
  },
  addButtonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '600',
  },
  emptyContainer: {
    alignItems: 'center',
    padding: 32,
  },
  emptyText: {
    fontSize: 18,
    fontWeight: '600',
    color: '#6C757D',
    marginBottom: 8,
  },
  emptySubtext: {
    fontSize: 14,
    color: '#ADB5BD',
    textAlign: 'center',
  },
  subscriptionsList: {
    gap: 16,
  },
  subscriptionCard: {
    backgroundColor: '#F8F9FA',
    borderRadius: 8,
    padding: 16,
    borderWidth: 1,
    borderColor: '#E9ECEF',
  },
  subscriptionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  subscriptionPhone: {
    fontSize: 16,
    fontWeight: '600',
    color: '#212529',
  },
  statusBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
  },
  statusBadgeActive: {
    backgroundColor: '#D4EDDA',
  },
  statusBadgeInactive: {
    backgroundColor: '#F8D7DA',
  },
  statusText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#155724',
  },
  subscriptionMethod: {
    fontSize: 14,
    color: '#6C757D',
    marginBottom: 4,
  },
  subscriptionInfo: {
    fontSize: 13,
    color: '#6C757D',
    marginBottom: 4,
  },
  deleteButton: {
    alignSelf: 'flex-end',
    marginTop: 8,
    paddingHorizontal: 12,
    paddingVertical: 6,
  },
  deleteButtonText: {
    color: '#DC3545',
    fontSize: 14,
    fontWeight: '600',
  },
});

