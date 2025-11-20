// test-utils/mockFetch.js
import { apiClient } from '../services/api';

export function mockApiClient({
  transactions = [],
  allocation = [],
  performance = [],
} = {}) {
  // Mock the apiClient.get method
  jest.spyOn(apiClient, 'get').mockImplementation((url) => {
    // Transactions API
    if (url.includes("/transactions/")) {
      return Promise.resolve({ data: { transactions } });
    }

    // Portfolio allocation API
    if (url.includes("/portfolio/") && !url.includes("/performance/")) {
      return Promise.resolve({ data: { allocation } });
    }

    // Portfolio performance API
    if (url.includes("/portfolio/performance/")) {
      return Promise.resolve({ data: { performance } });
    }

    // IRX benchmark API
    if (url.includes("/entities/ticker=^IRX/chart")) {
      return Promise.resolve({
        data: {
          stock_chart: {
            dates: ["2024-01-01", "2024-06-01"],
            prices: [5, 7],
          },
        },
      });
    }

    // Default: unknown endpoint
    return Promise.reject(new Error(`Unhandled API URL: ${url}`));
  });
}
