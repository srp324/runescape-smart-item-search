/**
 * API Client for React web app to communicate with FastAPI backend.
 * Uses fetch API for HTTP requests.
 */

const API_BASE_URL = import.meta.env.DEV
  ? 'http://localhost:8000'  // Development
  : import.meta.env.VITE_API_URL || 'https://your-production-api.com';  // Production

export interface Item {
  item_id: number;
  name: string;
  examine: string | null;
  members: boolean;
  lowalch: number | null;
  highalch: number | null;
  limit: number | null;
  value: number | null;
  icon: string | null;
  created_at: string;
  updated_at: string;
}

export interface SearchResult {
  item: Item;
  similarity: number;
}

export interface SearchResponse {
  results: SearchResult[];
  total: number;
  query: string;
}

export interface SearchRequest {
  query: string;
  limit?: number;
  members_only?: boolean;
}

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  /**
   * Generic fetch wrapper with error handling.
   */
  private async fetch<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    
    try {
      const response = await fetch(url, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
      });

      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
        throw new Error(error.detail || `HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      if (error instanceof Error) {
        throw error;
      }
      throw new Error('Network error: Unable to connect to server');
    }
  }

  /**
   * Search items using vector similarity.
   */
  async searchItems(request: SearchRequest): Promise<SearchResponse> {
    return this.fetch<SearchResponse>('/api/items/search', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  /**
   * Get a specific item by ID.
   */
  async getItem(itemId: number): Promise<Item> {
    return this.fetch<Item>(`/api/items/${itemId}`);
  }

  /**
   * List items with optional filters.
   */
  async listItems(options: {
    members_only?: boolean;
    limit?: number;
    offset?: number;
  } = {}): Promise<Item[]> {
    const params = new URLSearchParams();
    if (options.members_only !== undefined) params.append('members_only', options.members_only.toString());
    if (options.limit) params.append('limit', options.limit.toString());
    if (options.offset) params.append('offset', options.offset.toString());

    const queryString = params.toString();
    const endpoint = queryString ? `/api/items?${queryString}` : '/api/items';
    
    return this.fetch<Item[]>(endpoint);
  }

  /**
   * Get price history for an item.
   */
  async getItemPriceHistory(itemId: number, limit: number = 100): Promise<any[]> {
    return this.fetch<any[]>(`/api/items/${itemId}/prices?limit=${limit}`);
  }

  /**
   * Get current price for an item.
   */
  async getCurrentItemPrice(itemId: number): Promise<{
    item_id: number;
    name: string;
    high_price: number | null;
    low_price: number | null;
    timestamp: string;
  }> {
    return this.fetch(`/api/items/${itemId}/price/current`);
  }

  /**
   * Health check endpoint.
   */
  async healthCheck(): Promise<{
    status: string;
    database: string;
    pgvector: string;
  }> {
    return this.fetch('/health');
  }
}

// Export singleton instance
export const apiClient = new ApiClient();

// Export class for custom instances
export default ApiClient;

