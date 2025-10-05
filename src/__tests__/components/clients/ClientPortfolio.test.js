import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import PortfolioDashboard from "../../../components/clients/ClientPortfolio";
import { mockFetchPortfolioAndTransactions } from "../../../test-utils/mockFetch";

describe("PortfolioDashboard", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test("renders portfolio and transactions correctly", async () => {
    const mockData = {
      allocation: [
        { name: "AAPL", value: 80, color: "#6366f1" },
        { name: "HSBC", value: 41, color: "#10b981" },
        { name: "TSMC", value: 35, color: "#f59e0b" },
      ],
      performance: [
        { date: "2024-01-01", value: 5000 },
        { date: "2024-06-01", value: 7000 },
      ],
      transactions: [
        {
          txn_uuid: "txn-1",
          datetime: "2025-01-01T10:00:00Z",
          source: "Bank",
          type: "Deposit",
          currency: "SGD",
          amount: 5000,
          status: "Completed",
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
          desc: "Bought AAPL",
        },
      ],
    };

    mockFetchPortfolioAndTransactions(mockData);

    render(<PortfolioDashboard clientId="123" />);

    // Wait for portfolio data to load
    await waitFor(() =>
      expect(screen.getByText(/Portfolio Performance/i)).toBeInTheDocument()
    );

    // ✅ Check allocations dynamically
    mockData.allocation.forEach(({ name, value }) => {
      expect(screen.getByText(name)).toBeInTheDocument();
      expect(screen.getByText(value.toString())).toBeInTheDocument();
    });
  });

  test("handles time range change", async () => {
    const mockData = {
      allocation: [{ name: "TSMC", value: 200, color: "#f59e0b" }],
      performance: [
        { date: "2024-01-01", value: 3000 },
        { date: "2024-06-01", value: 6000 },
      ],
      transactions: [],
    };

    mockFetchPortfolioAndTransactions(mockData);

    render(<PortfolioDashboard clientId="123" />);

    await waitFor(() =>
      expect(screen.getByText(/Portfolio Performance/i)).toBeInTheDocument()
    );

    // Change time range
    const button3M = screen.getByRole("button", { name: "3M" });
    fireEvent.click(button3M);

    // Verify state updated (chart still present)
    expect(await screen.findByText(/Portfolio Performance/i)).toBeInTheDocument();
  });
});
