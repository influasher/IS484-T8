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

    // ✅ Handle IRX benchmark fetch
    if (url.includes("/entities/ticker=^IRX/chart")) {
      return Promise.resolve({
        ok: true,
        json: () =>
          Promise.resolve({
            data: {
              stock_chart: {
                dates: ["2024-01-01", "2024-06-01"],
                prices: [5, 7],
              },
            },
          }),
      });
    }

    // Default fallback for unknown endpoints
    return Promise.reject(new Error(`Unhandled fetch URL: ${url}`));
  });
}
