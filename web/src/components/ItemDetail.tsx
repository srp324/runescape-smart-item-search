/**
 * React component for displaying detailed item information with charts and metrics.
 */

import React, { useState, useEffect, useMemo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine
} from 'recharts';
import { apiClient, Item, PriceHistory, ItemPriceResponse } from '../apiClient';
import './ItemDetail.css';

type TimeRange = '1h' | '6h' | '24h' | '7d' | '30d';

const ItemDetail: React.FC = () => {
  const { itemId } = useParams<{ itemId: string }>();
  const navigate = useNavigate();
  const [item, setItem] = useState<Item | null>(null);
  const [currentPrice, setCurrentPrice] = useState<ItemPriceResponse | null>(null);
  const [priceHistory, setPriceHistory] = useState<PriceHistory[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [timeRange, setTimeRange] = useState<TimeRange>('24h');

  useEffect(() => {
    const fetchItemData = async () => {
      if (!itemId) return;

      setLoading(true);
      setError(null);

      try {
        const id = parseInt(itemId, 10);
        const [itemData, priceData] = await Promise.all([
          apiClient.getItem(id),
          apiClient.getCurrentItemPrice(id).catch(() => null)
        ]);

        setItem(itemData);
        setCurrentPrice(priceData);

        // Fetch price history (up to 1000 entries, we'll filter by time range on client)
        const history = await apiClient.getItemPriceHistory(id, 1000);
        setPriceHistory(history.reverse()); // Reverse to show chronological order
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load item data');
      } finally {
        setLoading(false);
      }
    };

    fetchItemData();
  }, [itemId]);

  // Filter price history based on selected time range
  const filteredPriceHistory = useMemo(() => {
    if (!priceHistory.length) return [];

    const now = new Date();
    const timeRanges: Record<TimeRange, number> = {
      '1h': 60 * 60 * 1000,
      '6h': 6 * 60 * 60 * 1000,
      '24h': 24 * 60 * 60 * 1000,
      '7d': 7 * 24 * 60 * 60 * 1000,
      '30d': 30 * 24 * 60 * 60 * 1000,
    };

    const cutoffTime = now.getTime() - timeRanges[timeRange];
    return priceHistory.filter((entry) => {
      const entryTime = new Date(entry.timestamp).getTime();
      return entryTime >= cutoffTime;
    });
  }, [priceHistory, timeRange]);

  // Format data for charts
  const chartData = useMemo(() => {
    return filteredPriceHistory.map((entry) => ({
      time: new Date(entry.timestamp),
      timestamp: entry.timestamp,
      buyPrice: entry.high_price,
      sellPrice: entry.low_price,
      margin: entry.high_price && entry.low_price 
        ? entry.high_price - entry.low_price 
        : null,
    }));
  }, [filteredPriceHistory]);

  // Calculate statistics
  const stats = useMemo(() => {
    if (!currentPrice || !chartData.length) {
      return {
        dailyVolume: null,
        margin: null,
        potentialProfit: null,
        marginVolume: null,
        roi: null,
      };
    }

    const latest = currentPrice;
    const margin = latest.high_price && latest.low_price 
      ? latest.high_price - latest.low_price 
      : null;
    
    // Estimate daily volume based on price data points (rough approximation)
    // Since we don't have actual volume data, we'll use a placeholder
    const dailyVolume = chartData.length * 60; // Rough estimate based on data frequency
    
    const buyLimit = item?.limit || 0;
    const potentialProfit = margin && buyLimit ? margin * buyLimit : null;
    const marginVolume = margin && dailyVolume ? margin * dailyVolume : null;
    const roi = margin && latest.low_price ? (margin / latest.low_price) * 100 : null;

    return {
      dailyVolume,
      margin,
      potentialProfit,
      marginVolume,
      roi,
    };
  }, [currentPrice, chartData, item]);

  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  };

  const formatTimeAgo = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    
    if (diffMins < 1) return 'just now';
    if (diffMins === 1) return 'a minute ago';
    if (diffMins < 60) return `${diffMins} minutes ago`;
    
    const diffHours = Math.floor(diffMins / 60);
    if (diffHours === 1) return 'an hour ago';
    if (diffHours < 24) return `${diffHours} hours ago`;
    
    const diffDays = Math.floor(diffHours / 24);
    if (diffDays === 1) return 'a day ago';
    return `${diffDays} days ago`;
  };

  const formatCurrency = (value: number | null) => {
    if (value === null) return 'N/A';
    return value.toLocaleString('en-US') + ' coins';
  };

  const formatNumber = (value: number | null) => {
    if (value === null) return 'N/A';
    return value.toLocaleString('en-US');
  };

  if (loading) {
    return (
      <div className="item-detail-container">
        <div className="loading-container">
          <p>Loading item data...</p>
        </div>
      </div>
    );
  }

  if (error || !item) {
    return (
      <div className="item-detail-container">
        <div className="error-container">
          <p className="error-text">Error: {error || 'Item not found'}</p>
          <button onClick={() => navigate('/')} className="back-button">
            Back to Search
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="item-detail-container">
      <button onClick={() => navigate('/')} className="back-button">
        ← Back to Search
      </button>

      <div className="item-detail-header">
        <div className="item-title-section">
          <h1 className="item-name">{item.name}</h1>
          <span className="item-id">(Item ID: {item.item_id})</span>
        </div>
        <div className="item-actions">
          <a
            href={`https://oldschool.runescape.wiki/w/${encodeURIComponent(item.name)}`}
            target="_blank"
            rel="noopener noreferrer"
            className="action-link"
          >
            Wiki
          </a>
          <a
            href={`https://www.osrsbox.com/tools/item-database/#${item.item_id}`}
            target="_blank"
            rel="noopener noreferrer"
            className="action-link"
          >
            GEDB
          </a>
          <button className="action-icon" title="Bookmark">🔖</button>
          <button className="action-icon" title="Favorite">❤️</button>
        </div>
      </div>

      <div className="item-detail-content">
        <div className="item-info-grid">
          {/* Left Column - Trade Information */}
          <div className="info-column">
            <h3 className="column-title">Trade Information</h3>
            <div className="price-info">
              <div className="price-item">
                <span className="price-label">Buy price:</span>
                <span className="price-value">
                  {formatCurrency(currentPrice?.high_price ?? null)}
                </span>
                {currentPrice?.timestamp && (
                  <span className="price-timestamp">
                    Last trade: {formatTimeAgo(currentPrice.timestamp)}
                  </span>
                )}
              </div>
              <div className="price-item">
                <span className="price-label">Sell price:</span>
                <span className="price-value">
                  {formatCurrency(currentPrice?.low_price ?? null)}
                </span>
                {currentPrice?.timestamp && (
                  <span className="price-timestamp">
                    Last trade: {formatTimeAgo(currentPrice.timestamp)}
                  </span>
                )}
              </div>
            </div>
          </div>

          {/* Middle Column - Market Statistics */}
          <div className="info-column">
            <h3 className="column-title">Market Statistics</h3>
            <div className="stats-grid">
              <div className="stat-item">
                <span className="stat-label">Daily volume:</span>
                <span className="stat-value volume">
                  {formatNumber(stats.dailyVolume)}
                </span>
                <span className="stat-note">Based on available price data</span>
              </div>
              <div className="stat-item">
                <span className="stat-label">Margin:</span>
                <span className="stat-value">{formatNumber(stats.margin)}</span>
              </div>
              <div className="stat-item">
                <span className="stat-label">Potential profit:</span>
                <span className="stat-value">{formatNumber(stats.potentialProfit)}</span>
              </div>
              <div className="stat-item">
                <span className="stat-label">Margin * volume:</span>
                <span className="stat-value">{formatNumber(stats.marginVolume)}</span>
              </div>
              <div className="stat-item">
                <span className="stat-label">ROI:</span>
                <span className="stat-value">
                  {stats.roi !== null ? `${stats.roi.toFixed(2)}%` : 'N/A'}
                </span>
              </div>
            </div>
          </div>

          {/* Right Column - Item Details */}
          <div className="info-column">
            <div className="time-range-selector">
              <select
                value={timeRange}
                onChange={(e) => setTimeRange(e.target.value as TimeRange)}
                className="time-select"
              >
                <option value="1h">1 hour</option>
                <option value="6h">6 hours</option>
                <option value="24h">1 day</option>
                <option value="7d">7 days</option>
                <option value="30d">30 days</option>
              </select>
            </div>
            <h3 className="column-title">Item Details</h3>
            <div className="details-list">
              {item.limit !== null && (
                <div className="detail-item">
                  <span className="detail-label">Buy limit:</span>
                  <span className="detail-value">{formatNumber(item.limit)}</span>
                </div>
              )}
              {item.highalch !== null && (
                <div className="detail-item">
                  <span className="detail-label">High alch:</span>
                  <span className="detail-value">
                    {formatNumber(item.highalch)}
                    {currentPrice?.low_price && (
                      <span className="alch-diff">
                        {' '}({item.highalch - currentPrice.low_price})
                      </span>
                    )}
                  </span>
                </div>
              )}
              {item.lowalch !== null && (
                <div className="detail-item">
                  <span className="detail-label">Low alch:</span>
                  <span className="detail-value">{formatNumber(item.lowalch)}</span>
                </div>
              )}
              <div className="detail-item">
                <span className="detail-label">Members:</span>
                <span className="detail-value">
                  {item.members ? '⭐ Yes' : 'No'}
                </span>
              </div>
              {item.examine && (
                <div className="detail-item">
                  <span className="detail-label">Examine:</span>
                  <span className="detail-value examine">{item.examine}</span>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Charts Section */}
        <div className="charts-section">
          {/* Price Chart */}
          <div className="chart-container">
            <h2 className="chart-title">Price</h2>
            <p className="chart-instruction">
              Displaying data at {timeRange} intervals.
            </p>
            {chartData.length > 0 ? (
              <ResponsiveContainer width="100%" height={400}>
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#444" />
                  <XAxis
                    dataKey="time"
                    stroke="#ccc"
                    tickFormatter={(time) => {
                      const date = new Date(time);
                      const hours = date.getHours().toString().padStart(2, '0');
                      const minutes = date.getMinutes().toString().padStart(2, '0');
                      const month = date.toLocaleString('en-US', { month: 'short' });
                      const day = date.getDate();
                      const year = date.getFullYear();
                      return `${hours}:${minutes} ${month} ${day}, ${year}`;
                    }}
                  />
                  <YAxis stroke="#ccc" tickFormatter={(value) => value.toLocaleString()} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#2a2a2a', border: '1px solid #444' }}
                    labelFormatter={(time) => formatTime(time)}
                    formatter={(value: number) => formatCurrency(value)}
                  />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="buyPrice"
                    stroke="#ff9800"
                    strokeWidth={2}
                    dot={false}
                    name="Buy Price"
                  />
                  <Line
                    type="monotone"
                    dataKey="sellPrice"
                    stroke="#4caf50"
                    strokeWidth={2}
                    dot={false}
                    name="Sell Price"
                  />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <div className="no-data-message">No price data available for this time range</div>
            )}
          </div>

          {/* Margin Chart */}
          <div className="chart-container">
            <h2 className="chart-title">Margin</h2>
            <p className="chart-instruction">
              Displaying data at {timeRange} intervals.
            </p>
            {chartData.length > 0 ? (
              <ResponsiveContainer width="100%" height={400}>
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#444" />
                  <XAxis
                    dataKey="time"
                    stroke="#ccc"
                    tickFormatter={(time) => {
                      const date = new Date(time);
                      const hours = date.getHours().toString().padStart(2, '0');
                      const minutes = date.getMinutes().toString().padStart(2, '0');
                      const month = date.toLocaleString('en-US', { month: 'short' });
                      const day = date.getDate();
                      const year = date.getFullYear();
                      return `${hours}:${minutes} ${month} ${day}, ${year}`;
                    }}
                  />
                  <YAxis stroke="#ccc" tickFormatter={(value) => value.toLocaleString()} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#2a2a2a', border: '1px solid #444' }}
                    labelFormatter={(time) => formatTime(time)}
                    formatter={(value: number) => formatCurrency(value)}
                  />
                  <Legend />
                  <ReferenceLine y={0} stroke="#666" />
                  <Line
                    type="monotone"
                    dataKey="margin"
                    stroke="#2196f3"
                    strokeWidth={2}
                    dot={false}
                    name="Margin"
                  />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <div className="no-data-message">No margin data available for this time range</div>
            )}
          </div>

          {/* Volume Chart Placeholder */}
          <div className="chart-container">
            <h2 className="chart-title">Volume</h2>
            <p className="chart-instruction">
              Volume data is not currently available. This chart will display trading volume once data is collected.
            </p>
            <div className="no-data-message">
              Volume data is not available in the current dataset. The OSRS Wiki API provides price data but not trading volume information.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ItemDetail;
