// test-utils/mockFetch.js
export function mockFetchPortfolioAndTransactions({
    transactions = [],
    allocation = [],
    performance = [],
  } = {}) {
    global.fetch = jest.fn((url) => {
      // Transactions API
      if (url.includes("/transactions/")) {
        return Promise.resolve({
          ok: true,
          json: async () => ({ transactions }),
        });
      }
  
      // Portfolio allocation API
      if (url.includes("/portfolio/")) {
        return Promise.resolve({
          ok: true,
          json: async () => ({ allocation }),
        });
      }
  
      // Portfolio performance API
      if (url.includes("/portfolio/performance/")) {
        return Promise.resolve({
          ok: true,
          json: async () => ({ performance }),
        });
      }
  
      // Default fallback for unknown endpoints
      return Promise.reject(new Error(`Unhandled fetch URL: ${url}`));
    });
  }
  