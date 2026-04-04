/**
 * API Client with Retry Logic and Error Handling
 */

import config from '@/lib/config';

export class ApiError extends Error {
  constructor(
    message: string,
    public statusCode?: number,
    public details?: any
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

interface FetchOptions extends RequestInit {
  timeout?: number;
  retries?: number;
}

/**
 * Fetch with timeout support
 */
async function fetchWithTimeout(
  url: string,
  options: FetchOptions = {}
): Promise<Response> {
  const { timeout = config.apiTimeout, ...fetchOptions } = options;

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);

  try {
    const response = await fetch(url, {
      ...fetchOptions,
      signal: controller.signal,
    });
    clearTimeout(timeoutId);
    return response;
  } catch (error) {
    clearTimeout(timeoutId);
    if (error instanceof Error && error.name === 'AbortError') {
      throw new ApiError('Request timeout', 408);
    }
    throw error;
  }
}

/**
 * Fetch with retry logic
 */
async function fetchWithRetry(
  url: string,
  options: FetchOptions = {}
): Promise<Response> {
  const { retries = config.maxRetries, ...fetchOptions } = options;
  let lastError: Error | null = null;

  for (let attempt = 0; attempt <= retries; attempt++) {
    try {
      const response = await fetchWithTimeout(url, fetchOptions);
      
      // Don't retry on client errors (4xx)
      if (response.status >= 400 && response.status < 500) {
        return response;
      }
      
      // Success or server error that we might retry
      if (response.ok || attempt === retries) {
        return response;
      }
      
      // Wait before retry
      if (attempt < retries) {
        await new Promise(resolve => setTimeout(resolve, config.retryDelay * (attempt + 1)));
      }
    } catch (error) {
      lastError = error as Error;
      
      // Don't retry on network errors on last attempt
      if (attempt === retries) {
        throw error;
      }
      
      // Wait before retry
      await new Promise(resolve => setTimeout(resolve, config.retryDelay * (attempt + 1)));
    }
  }

  throw lastError || new Error('Unknown error');
}

/**
 * Main API client
 */
export const apiClient = {
  /**
   * GET request with type safety
   */
  async get<T>(endpoint: string, options: FetchOptions = {}): Promise<T> {
    const url = `${config.apiUrl}${endpoint}`;
    
    try {
      const response = await fetchWithRetry(url, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
        ...options,
      });

      if (!response.ok) {
        let errorMessage = `HTTP ${response.status}: ${response.statusText}`;
        let errorDetails = null;

        try {
          const errorBody = await response.json();
          errorMessage = errorBody.message || errorBody.detail || errorMessage;
          errorDetails = errorBody;
        } catch {
          // Ignore JSON parse errors
        }

        throw new ApiError(errorMessage, response.status, errorDetails);
      }

      const data = await response.json();
      return data as T;
    } catch (error) {
      if (error instanceof ApiError) {
        throw error;
      }
      
      if (error instanceof Error) {
        if (error.message.includes('fetch')) {
          throw new ApiError('Network error: Unable to connect to backend', 0);
        }
        throw new ApiError(error.message);
      }
      
      throw new ApiError('Unknown error occurred');
    }
  },

  /**
   * POST request with type safety
   */
  async post<T>(endpoint: string, body: any, options: FetchOptions = {}): Promise<T> {
    const url = `${config.apiUrl}${endpoint}`;
    
    try {
      const response = await fetchWithRetry(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
        body: JSON.stringify(body),
        ...options,
      });

      if (!response.ok) {
        let errorMessage = `HTTP ${response.status}: ${response.statusText}`;
        let errorDetails = null;

        try {
          const errorBody = await response.json();
          errorMessage = errorBody.message || errorBody.detail || errorMessage;
          errorDetails = errorBody;
        } catch {
          // Ignore JSON parse errors
        }

        throw new ApiError(errorMessage, response.status, errorDetails);
      }

      const data = await response.json();
      return data as T;
    } catch (error) {
      if (error instanceof ApiError) {
        throw error;
      }
      
      if (error instanceof Error) {
        if (error.message.includes('fetch')) {
          throw new ApiError('Network error: Unable to connect to backend', 0);
        }
        throw new ApiError(error.message);
      }
      
      throw new ApiError('Unknown error occurred');
    }
  },

  /**
   * Check backend health
   */
  async healthCheck(): Promise<boolean> {
    try {
      await this.get('/api/health', { retries: 0, timeout: 3000 });
      return true;
    } catch {
      return false;
    }
  },
};

export default apiClient;
