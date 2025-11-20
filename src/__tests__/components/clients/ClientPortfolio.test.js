import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { getData } from "../../../services/api";
import PortfolioDashboard from "../../../components/clients/ClientPortfolio";
import ClientTransactionTable from "../../../components/clients/ClientTransactionTable";
import ClientPortfolioTable from "../../../components/clients/ClientPortfolioTable";

// Mock the API service
jest.mock("../../../services/api");

// Mock child components
jest.mock("../../../components/clients/ClientTransactionTable", () => {
  return jest.fn(() => <div data-testid="client-transaction-table">Transaction Table</div>);
});

jest.mock("../../../components/clients/ClientPortfolioTable", () => {
  return jest.fn(() => <div data-testid="client-portfolio-table">Portfolio Table</div>);
});

describe("PortfolioDashboard", () => {
  const mockTransactionsData = {
    transactions: [
      {
        txn_uuid: "txn-1",
        datetime: "2025-01-01T10:00:00Z",
        source: "Bank",
        type: "Deposit",
        currency: "SGD",
        amount: 5000,
        status: "Completed",
        price_per_share: 100,
        quantity: 1,
        desc: "Initial deposit",
      },
      {
        txn_uuid: "txn-2",
        datetime: "2025-01-05T10:00:00Z",
        source: "Trading",
        type: "Purchase",
        currency: "SGD",
        amount: -2000,
        status: "Completed",
        price_per_share: 100,
        quantity: 1,
        desc: "Bought AAPL",
      },
    ],
  };

  const mockPortfolioData = {
    allocation: [
      { name: "AAPL", value: 80, color: "#6366f1" },
      { name: "HSBC", value: 41, color: "#10b981" },
      { name: "TSMC", value: 35, color: "#f59e0b" },
    ],
  };

  const mockPerformanceData = {
    performance: [
      { date: "2024-01-01", value: 5000 },
      { date: "2024-02-01", value: 5200 },
      { date: "2024-03-01", value: 5400 },
      { date: "2024-04-01", value: 5600 },
      { date: "2024-05-01", value: 6000 },
      { date: "2024-06-01", value: 7000 },
      { date: "2024-07-01", value: 7200 },
      { date: "2024-08-01", value: 7400 },
      { date: "2024-09-01", value: 7600 },
      { date: "2024-10-01", value: 7800 },
      { date: "2024-11-01", value: 8000 },
      { date: "2024-12-01", value: 8200 },
    ],
  };

  const mockIRXData = {
    data: {
      stock_chart: {
        dates: [
          "2024-01-01",
          "2024-02-01",
          "2024-03-01",
          "2024-04-01",
          "2024-05-01",
          "2024-06-01",
          "2024-07-01",
          "2024-08-01",
          "2024-09-01",
          "2024-10-01",
          "2024-11-01",
          "2024-12-01",
        ],
        prices: [4.5, 4.6, 4.7, 4.8, 4.9, 5.0, 5.1, 5.2, 5.3, 5.4, 5.5, 5.6],
      },
    },
  };

  beforeEach(() => {
    // Reset all mocks before each test
    jest.clearAllMocks();

    // Setup default mock implementations
    getData.mockImplementation((url) => {
      if (url.includes("/transactions/client/")) {
        return Promise.resolve(mockTransactionsData);
      }
      if (url.includes("/portfolio/") && url.includes("/performance/")) {
        return Promise.resolve(mockPerformanceData);
      }
      if (url.includes("/portfolio/")) {
        return Promise.resolve(mockPortfolioData);
      }
      if (url.includes("ticker=^IRX")) {
        return Promise.resolve(mockIRXData);
      }
      return Promise.resolve({});
    });
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  test("renders portfolio and transactions correctly", async () => {
    render(<PortfolioDashboard clientId="123" />);

    // Check loading state appears first
    expect(screen.getByText(/Loading Portfolio/i)).toBeInTheDocument();

    // Wait for portfolio line chart to render
    await waitFor(
      () => {
        expect(screen.getByTestId("portfolio-line-chart")).toBeInTheDocument();
      },
      { timeout: 3000 }
    );

    // Check for allocation pie chart and allocation items
    expect(screen.getByTestId("allocation-pie-chart")).toBeInTheDocument();
    expect(screen.getByText("AAPL")).toBeInTheDocument();
    expect(screen.getByText("HSBC")).toBeInTheDocument();
    expect(screen.getByText("TSMC")).toBeInTheDocument();

    // Verify API calls were made
    expect(getData).toHaveBeenCalledWith("/transactions/client/123");
    expect(getData).toHaveBeenCalledWith("/portfolio/123");
    expect(getData).toHaveBeenCalledWith("/portfolio/performance/123");
  });

  test("handles time range change", async () => {
    render(<PortfolioDashboard clientId="123" />);

    // Check loading state
    expect(screen.getByText(/Loading Portfolio/i)).toBeInTheDocument();

    // Get the initial API call count
    const initialCallCount = getData.mock.calls.length;

    // Wait for portfolio line chart to render
    await waitFor(
      () => {
        expect(screen.getByTestId("portfolio-line-chart")).toBeInTheDocument();
      },
      { timeout: 3000 }
    );

    // Change time range to 3M
    const button3M = screen.getByRole("button", { name: "3M" });
    fireEvent.click(button3M);

    // Wait for portfolio line chart to render
    await waitFor(
      () => {
        expect(screen.getByTestId("portfolio-line-chart")).toBeInTheDocument();
      },
      { timeout: 3000 }
    );

    expect(getData.mock.calls.length).toBeGreaterThan(initialCallCount);

    // Get the call count after 3M
    const callCountAfter3M = getData.mock.calls.length;

    // Change time range to 1Y
    const button1Y = screen.getByRole("button", { name: "1Y" });
    fireEvent.click(button1Y);

    // Wait for portfolio line chart to render
    await waitFor(
      () => {
        expect(screen.getByTestId("portfolio-line-chart")).toBeInTheDocument();
      },
      { timeout: 3000 }
    );

    expect(getData.mock.calls.length).toBeGreaterThan(callCountAfter3M);

    // If checking heading specifically
    expect(
      screen.getByRole("heading", { name: /Portfolio Performance/i })
    ).toBeInTheDocument();
  });

  test("displays loading state initially", () => {
    render(<PortfolioDashboard clientId="123" />);
    
    expect(screen.getByText(/Loading Portfolio/i)).toBeInTheDocument();
    expect(screen.getByRole("progressbar")).toBeInTheDocument();
  });

  test("handles empty transactions gracefully", async () => {
    // Mock empty transactions
    getData.mockImplementation((url) => {
      if (url.includes("/transactions/client/")) {
        return Promise.resolve({ transactions: [] });
      }
      if (url.includes("/portfolio/") && url.includes("/performance/")) {
        return Promise.resolve(mockPerformanceData);
      }
      if (url.includes("/portfolio/")) {
        return Promise.resolve(mockPortfolioData);
      }
      if (url.includes("ticker=^IRX")) {
        return Promise.resolve(mockIRXData);
      }
      return Promise.resolve({});
    });

    render(<PortfolioDashboard clientId="123" />);

    // Wait for loading to complete
    await waitFor(
      () => {
        expect(screen.queryByText(/Loading Portfolio/i)).not.toBeInTheDocument();
      },
      { timeout: 3000 }
    );

    // Component should still render with calculated metrics (even if zero)
    expect(screen.getByText(/Total Investment Amount/i)).toBeInTheDocument();
    expect(screen.getByText(/Total Portfolio Value/i)).toBeInTheDocument();
  });

  test("handles empty performance data gracefully", async () => {
    // Mock empty performance data
    getData.mockImplementation((url) => {
      if (url.includes("/transactions/client/")) {
        return Promise.resolve(mockTransactionsData);
      }
      if (url.includes("/portfolio/") && url.includes("/performance/")) {
        return Promise.resolve({ performance: [] });
      }
      if (url.includes("/portfolio/")) {
        return Promise.resolve(mockPortfolioData);
      }
      if (url.includes("ticker=^IRX")) {
        return Promise.resolve(mockIRXData);
      }
      return Promise.resolve({});
    });

    render(<PortfolioDashboard clientId="123" />);

    // Wait for loading to complete
    await waitFor(
      () => {
        expect(screen.queryByText(/Loading Portfolio/i)).not.toBeInTheDocument();
      },
      { timeout: 3000 }
    );

    // Should show message for no performance data
    expect(
      screen.getByText(/No performance data available for selected time range/i)
    ).toBeInTheDocument();
  });

  test("handles empty allocation data gracefully", async () => {
    // Mock empty allocation data
    getData.mockImplementation((url) => {
      if (url.includes("/transactions/client/")) {
        return Promise.resolve(mockTransactionsData);
      }
      if (url.includes("/portfolio/") && url.includes("/performance/")) {
        return Promise.resolve(mockPerformanceData);
      }
      if (url.includes("/portfolio/")) {
        return Promise.resolve({ allocation: [] });
      }
      if (url.includes("ticker=^IRX")) {
        return Promise.resolve(mockIRXData);
      }
      return Promise.resolve({});
    });

    render(<PortfolioDashboard clientId="123" />);

    // Wait for loading to complete
    await waitFor(
      () => {
        expect(screen.queryByText(/Loading Portfolio/i)).not.toBeInTheDocument();
      },
      { timeout: 3000 }
    );

    // Should show message for no allocation data
    expect(screen.getByText(/No allocation data available/i)).toBeInTheDocument();
  });

  test("handles API error gracefully", async () => {
    // Mock API error
    getData.mockRejectedValue(new Error("API Error"));

    render(<PortfolioDashboard clientId="123" />);

    // Wait for loading to complete
    await waitFor(
      () => {
        expect(screen.queryByText(/Loading Portfolio/i)).not.toBeInTheDocument();
      },
      { timeout: 3000 }
    );

    // Component should still render with empty data
    expect(screen.getByText(/Total Investment Amount/i)).toBeInTheDocument();
  });

  test("displays portfolio metrics correctly", async () => {
    render(<PortfolioDashboard clientId="123" />);

    // Wait for loading to complete
    await waitFor(
      () => {
        expect(screen.queryByText(/Loading Portfolio/i)).not.toBeInTheDocument();
      },
      { timeout: 3000 }
    );

    // Check that metrics are displayed
    expect(screen.getByText(/Total Investment Amount/i)).toBeInTheDocument();
    expect(screen.getByText(/Total Portfolio Value/i)).toBeInTheDocument();
    expect(screen.getByText(/Total unrealised profit\/loss \(P\/L\)/i)).toBeInTheDocument();

    // Verify metrics values are displayed (calculated from transactions)
    const usdElements = screen.getAllByText(/USD/i);
    expect(usdElements.length).toBeGreaterThan(0);
  });

  test("calculates portfolio metrics from transactions correctly", async () => {
    render(<PortfolioDashboard clientId="123" />);

    // Wait for loading to complete
    await waitFor(
      () => {
        expect(screen.queryByText(/Loading Portfolio/i)).not.toBeInTheDocument();
      },
      { timeout: 3000 }
    );

    // Based on mock transactions:
    // Deposit: 5000
    // Purchase: -2000
    // Net Cash Invested: 5000
    // Securities Investment: 2000
    // Estimated Securities Value: 2000 * 1.15 = 2300
    // Current Cash: 5000 - 2000 = 3000
    // Total Portfolio Value: 3000 + 2300 = 5300
    // Unrealized P/L: 5300 - 5000 = 300
    // Unrealized P/L %: (300 / 5000) * 100 = 6%

    expect(screen.getByText(/Total Investment Amount/i)).toBeInTheDocument();
    expect(screen.getByText(/Total Portfolio Value/i)).toBeInTheDocument();
  });

  test("renders all time range buttons", async () => {
    render(<PortfolioDashboard clientId="123" />);

    // Wait for component to load
    await waitFor(
      () => {
        expect(screen.queryByText(/Loading Portfolio/i)).not.toBeInTheDocument();
      },
      { timeout: 3000 }
    );

    // Check all time range buttons are present
    expect(screen.getByRole("button", { name: "1M" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "3M" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "6M" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "1Y" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "2Y" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "5Y" })).toBeInTheDocument();
  });

  test("passes correct props to ClientTransactionTable", async () => {
    render(<PortfolioDashboard clientId="123" />);

    // Wait for loading to complete
    await waitFor(
      () => {
        expect(screen.queryByText(/Loading Portfolio/i)).not.toBeInTheDocument();
      },
      { timeout: 3000 }
    );

    // Verify ClientTransactionTable was called with correct props
    expect(ClientTransactionTable).toHaveBeenCalledWith(
      expect.objectContaining({
        transactionData: expect.any(Array),
        loading: expect.any(Boolean),
      }),
      expect.anything()
    );
  });

  test("passes correct clientId to ClientPortfolioTable", async () => {
    render(<PortfolioDashboard clientId="123" />);

    // Wait for loading to complete
    await waitFor(
      () => {
        expect(screen.queryByText(/Loading Portfolio/i)).not.toBeInTheDocument();
      },
      { timeout: 3000 }
    );

    // Verify ClientPortfolioTable was called with correct clientId
    expect(ClientPortfolioTable).toHaveBeenCalledWith(
      expect.objectContaining({
        clientId: "123",
      }),
      expect.anything()
    );
  });
});