import React, {useState} from 'react';
import {View, Text, TouchableOpacity, StyleSheet, Linking} from 'react-native';
import {Source} from '../../types';

interface SourceCardProps {
  source: Source;
}

export const SourceCard: React.FC<SourceCardProps> = ({source}) => {
  const [expanded, setExpanded] = useState(false);

  const handlePress = async () => {
    if (source.url) {
      const supported = await Linking.canOpenURL(source.url);
      if (supported) {
        await Linking.openURL(source.url);
      }
    }
  };

  return (
    <View style={styles.container}>
      <TouchableOpacity
        onPress={() => setExpanded(!expanded)}
        style={styles.header}>
        <View style={styles.headerContent}>
          <Text style={styles.title} numberOfLines={expanded ? 0 : 1}>
            {source.title}
          </Text>
          <Text style={styles.category}>{source.category}</Text>
        </View>
        <Text style={styles.expandIcon}>{expanded ? '−' : '+'}</Text>
      </TouchableOpacity>

      {expanded && (
        <View style={styles.content}>
          {source.excerpt && (
            <Text style={styles.excerpt}>{source.excerpt}</Text>
          )}
          {source.url && (
            <TouchableOpacity onPress={handlePress} style={styles.linkButton}>
              <Text style={styles.linkText}>View Source</Text>
            </TouchableOpacity>
          )}
        </View>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#F8F9FA',
    borderRadius: 8,
    marginVertical: 4,
    borderWidth: 1,
    borderColor: '#E9ECEF',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 12,
  },
  headerContent: {
    flex: 1,
    marginRight: 8,
  },
  title: {
    fontSize: 14,
    fontWeight: '600',
    color: '#212529',
    marginBottom: 4,
  },
  category: {
    fontSize: 12,
    color: '#6C757D',
  },
  expandIcon: {
    fontSize: 18,
    color: '#6C757D',
    fontWeight: 'bold',
  },
  content: {
    padding: 12,
    paddingTop: 0,
    borderTopWidth: 1,
    borderTopColor: '#E9ECEF',
  },
  excerpt: {
    fontSize: 13,
    color: '#495057',
    lineHeight: 20,
    marginBottom: 8,
  },
  linkButton: {
    alignSelf: 'flex-start',
  },
  linkText: {
    fontSize: 13,
    color: '#007AFF',
    fontWeight: '600',
  },
});
