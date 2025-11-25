/**
 * React web component for item search.
 * Desktop version of the search screen.
 */

import React, { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiClient, SearchResult } from '../apiClient';
import './SearchScreen.css';

const SearchScreen: React.FC = () => {
  const navigate = useNavigate();
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [membersOnly, setMembersOnly] = useState<boolean | null>(null);

  const performSearch = useCallback(async (searchQuery: string, filterValue?: boolean | null) => {
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
        members_only: (filterValue !== undefined ? filterValue : membersOnly) ?? undefined,
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

  const handleKeyPress = useCallback((e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  }, [handleSearch]);

  return (
    <div className="search-container">
      <div className="search-header">
        <h1>RuneScape Smart Item Search</h1>
        <p className="subtitle">Search OSRS items using semantic search</p>
      </div>

      <div className="search-input-container">
        <input
          type="text"
          className="search-input"
          placeholder="Search OSRS items... (e.g., 'dragon longsword')"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyPress={handleKeyPress}
          autoCapitalize="off"
          autoCorrect="off"
        />
        
        <button
          className="search-button"
          onClick={handleSearch}
          disabled={loading}
        >
          {loading ? 'Searching...' : 'Search'}
        </button>
      </div>

      {/* Members filter */}
      <div className="filter-container">
        <button
          className={`filter-chip ${membersOnly === null ? 'active' : ''}`}
          onClick={() => {
            setMembersOnly(null);
            if (query) performSearch(query, null);
          }}
        >
          All Items
        </button>
        
        <button
          className={`filter-chip ${membersOnly === true ? 'active' : ''}`}
          onClick={() => {
            setMembersOnly(true);
            if (query) performSearch(query, true);
          }}
        >
          Members Only
        </button>
        
        <button
          className={`filter-chip ${membersOnly === false ? 'active' : ''}`}
          onClick={() => {
            setMembersOnly(false);
            if (query) performSearch(query, false);
          }}
        >
          Free-to-Play
        </button>
      </div>

      {error && (
        <div className="error-container">
          <p className="error-text">Error: {error}</p>
        </div>
      )}

      {results.length > 0 ? (
        <div className="results-container">
          <p className="result-count">
            Found {results.length} result{results.length !== 1 ? 's' : ''}
          </p>
          <div className="results-list">
            {results.map((result) => (
              <div
                key={result.item.item_id}
                className="item-card"
                onClick={() => navigate(`/item/${result.item.item_id}`)}
                style={{ cursor: 'pointer' }}
              >
                <div className="item-header">
                  <div className="item-name-container">
                    <h3 className="item-name">{result.item.name}</h3>
                    {result.item.members && (
                      <span className="members-badge">Members</span>
                    )}
                  </div>
                  <span className="similarity">
                    {(result.similarity * 100).toFixed(1)}% match
                  </span>
                </div>
                
                {result.item.examine && (
                  <p className="item-description">{result.item.examine}</p>
                )}
                
                <div className="item-meta">
                  {result.item.value !== null && (
                    <span className="meta-text">
                      💰 Value: {result.item.value.toLocaleString()} gp
                    </span>
                  )}
                  {result.item.highalch !== null && (
                    <span className="meta-text">
                      🔨 High Alch: {result.item.highalch.toLocaleString()} gp
                    </span>
                  )}
                  {result.item.limit !== null && (
                    <span className="meta-text">
                      📊 GE Limit: {result.item.limit.toLocaleString()}
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      ) : (
        !loading && query && (
          <div className="empty-container">
            <p className="empty-text">No results found</p>
            <p className="empty-subtext">Try a different search query</p>
          </div>
        )
      )}
    </div>
  );
};

export default SearchScreen;

