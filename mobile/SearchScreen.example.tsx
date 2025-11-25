/**
 * Example React Native screen for item search.
 * This demonstrates how to use the API client for vector search.
 */

import React, { useState, useCallback } from 'react';
import {
  View,
  Text,
  TextInput,
  FlatList,
  StyleSheet,
  ActivityIndicator,
  TouchableOpacity,
} from 'react-native';
import { apiClient, SearchResult } from './apiClient';

interface SearchScreenProps {
  // Add navigation props if needed
}

const SearchScreen: React.FC<SearchScreenProps> = () => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [membersOnly, setMembersOnly] = useState<boolean | null>(null);

  const performSearch = useCallback(async (searchQuery: string) => {
    if (!searchQuery.trim()) {
      setResults([]);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await apiClient.searchItems({
        query: searchQuery,
        limit: 20,
        members_only: membersOnly ?? undefined,
      });

      setResults(response.results);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Search failed');
      setResults([]);
    } finally {
      setLoading(false);
    }
  }, [membersOnly]);

  const handleSearch = useCallback(() => {
    performSearch(query);
  }, [query, performSearch]);

  const renderItem = ({ item }: { item: SearchResult }) => (
    <TouchableOpacity style={styles.itemCard}>
      <View style={styles.itemHeader}>
        <View style={styles.itemNameContainer}>
          <Text style={styles.itemName}>{item.item.name}</Text>
          {item.item.members && (
            <Text style={styles.membersBadge}>Members</Text>
          )}
        </View>
        <Text style={styles.similarity}>
          {(item.similarity * 100).toFixed(1)}% match
        </Text>
      </View>
      
      {item.item.examine && (
        <Text style={styles.itemDescription} numberOfLines={2}>
          {item.item.examine}
        </Text>
      )}
      
      <View style={styles.itemMeta}>
        {item.item.value !== null && (
          <Text style={styles.metaText}>
            💰 Value: {item.item.value.toLocaleString()} gp
          </Text>
        )}
        {item.item.highalch !== null && (
          <Text style={styles.metaText}>
            🔨 High Alch: {item.item.highalch.toLocaleString()} gp
          </Text>
        )}
        {item.item.limit !== null && (
          <Text style={styles.metaText}>
            📊 GE Limit: {item.item.limit.toLocaleString()}
          </Text>
        )}
      </View>
    </TouchableOpacity>
  );

  return (
    <View style={styles.container}>
      <View style={styles.searchContainer}>
        <TextInput
          style={styles.searchInput}
          placeholder="Search OSRS items... (e.g., 'dragon longsword')"
          value={query}
          onChangeText={setQuery}
          onSubmitEditing={handleSearch}
          returnKeyType="search"
          autoCapitalize="none"
          autoCorrect={false}
        />
        
        <TouchableOpacity
          style={styles.searchButton}
          onPress={handleSearch}
          disabled={loading}
        >
          {loading ? (
            <ActivityIndicator color="#fff" />
          ) : (
            <Text style={styles.searchButtonText}>Search</Text>
          )}
        </TouchableOpacity>
      </View>

      {/* Members filter */}
      <View style={styles.filterContainer}>
        <TouchableOpacity
          style={[
            styles.filterChip,
            membersOnly === null && styles.filterChipActive,
          ]}
          onPress={() => {
            setMembersOnly(null);
            if (query) performSearch(query);
          }}
        >
          <Text
            style={[
              styles.filterChipText,
              membersOnly === null && styles.filterChipTextActive,
            ]}
          >
            All Items
          </Text>
        </TouchableOpacity>
        
        <TouchableOpacity
          style={[
            styles.filterChip,
            membersOnly === true && styles.filterChipActive,
          ]}
          onPress={() => {
            setMembersOnly(true);
            if (query) performSearch(query);
          }}
        >
          <Text
            style={[
              styles.filterChipText,
              membersOnly === true && styles.filterChipTextActive,
            ]}
          >
            Members Only
          </Text>
        </TouchableOpacity>
        
        <TouchableOpacity
          style={[
            styles.filterChip,
            membersOnly === false && styles.filterChipActive,
          ]}
          onPress={() => {
            setMembersOnly(false);
            if (query) performSearch(query);
          }}
        >
          <Text
            style={[
              styles.filterChipText,
              membersOnly === false && styles.filterChipTextActive,
            ]}
          >
            Free-to-Play
          </Text>
        </TouchableOpacity>
      </View>

      {error && (
        <View style={styles.errorContainer}>
          <Text style={styles.errorText}>Error: {error}</Text>
        </View>
      )}

      {results.length > 0 ? (
        <FlatList
          data={results}
          renderItem={renderItem}
          keyExtractor={(item) => item.item.item_id.toString()}
          contentContainerStyle={styles.listContainer}
          ListHeaderComponent={
            <Text style={styles.resultCount}>
              Found {results.length} result{results.length !== 1 ? 's' : ''}
            </Text>
          }
        />
      ) : (
        !loading && query && (
          <View style={styles.emptyContainer}>
            <Text style={styles.emptyText}>No results found</Text>
            <Text style={styles.emptySubtext}>
              Try a different search query
            </Text>
          </View>
        )
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
    padding: 16,
  },
  searchContainer: {
    flexDirection: 'row',
    marginBottom: 16,
    gap: 8,
  },
  searchInput: {
    flex: 1,
    backgroundColor: '#fff',
    borderRadius: 8,
    padding: 12,
    fontSize: 16,
    borderWidth: 1,
    borderColor: '#ddd',
  },
  searchButton: {
    backgroundColor: '#007AFF',
    borderRadius: 8,
    paddingHorizontal: 24,
    justifyContent: 'center',
    alignItems: 'center',
    minWidth: 80,
  },
  searchButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  filterContainer: {
    flexDirection: 'row',
    marginBottom: 16,
    gap: 8,
    flexWrap: 'wrap',
  },
  filterChip: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    backgroundColor: '#fff',
    borderWidth: 1,
    borderColor: '#ddd',
  },
  filterChipActive: {
    backgroundColor: '#007AFF',
    borderColor: '#007AFF',
  },
  filterChipText: {
    fontSize: 14,
    color: '#333',
  },
  filterChipTextActive: {
    color: '#fff',
    fontWeight: '600',
  },
  errorContainer: {
    backgroundColor: '#ffebee',
    padding: 12,
    borderRadius: 8,
    marginBottom: 16,
  },
  errorText: {
    color: '#c62828',
    fontSize: 14,
  },
  listContainer: {
    paddingBottom: 16,
  },
  resultCount: {
    fontSize: 14,
    color: '#666',
    marginBottom: 12,
  },
  itemCard: {
    backgroundColor: '#fff',
    borderRadius: 8,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#e0e0e0',
  },
  itemHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  itemNameContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
    gap: 8,
  },
  itemName: {
    fontSize: 18,
    fontWeight: '600',
    color: '#333',
    flex: 1,
  },
  membersBadge: {
    fontSize: 10,
    fontWeight: '600',
    color: '#fff',
    backgroundColor: '#FF6B35',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
    overflow: 'hidden',
  },
  similarity: {
    fontSize: 12,
    color: '#007AFF',
    fontWeight: '600',
  },
  itemDescription: {
    fontSize: 14,
    color: '#666',
    marginBottom: 12,
  },
  itemMeta: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
  },
  metaText: {
    fontSize: 12,
    color: '#888',
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    marginTop: 64,
  },
  emptyText: {
    fontSize: 18,
    color: '#666',
    marginBottom: 8,
  },
  emptySubtext: {
    fontSize: 14,
    color: '#999',
  },
});

export default SearchScreen;

