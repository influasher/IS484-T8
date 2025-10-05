import {
  render,
  screen,
  fireEvent,
  waitFor,
  within,
} from "@testing-library/react";
import ClientTransactionTable from "../../../components/clients/ClientTransactionTable";

const mockTransactions = [
  {
    id: "txn-1",
    dateTime: "2025-01-01T10:00:00Z",
    source: "Bank",
    type: "DEPOSIT",
    currency: "SGD",
    amount: 5000,
    status: "Completed",
    description: "Initial deposit",
  },
  {
    id: "txn-2",
    dateTime: "2025-01-05T10:00:00Z",
    source: "Trading",
    type: "BUY",
    currency: "SGD",
    amount: -2000,
    status: "Completed",
    description: "Bought AAPL",
  },
  {
    id: "txn-3",
    dateTime: "2025-01-12T10:00:00Z",
    source: "Dividend Co",
    type: "DIVIDEND",
    currency: "SGD",
    amount: 50,
    status: "Completed",
    description: "Dividend from HSBC",
  },
];

describe("ClientTransactionTable", () => {
  test("renders table headers", () => {
    render(<ClientTransactionTable transactionData={mockTransactions} />);

    expect(screen.getByText(/Date/i)).toBeInTheDocument();
    expect(screen.getByText(/Source/i)).toBeInTheDocument();
    expect(screen.getByText(/Amount/i)).toBeInTheDocument();
    expect(screen.getByText(/Desc/i)).toBeInTheDocument();
  });

  test("renders transactions correctly in the active tab", async () => {
    render(<ClientTransactionTable transactionData={mockTransactions} />);

    // Wait for the tab and summary to render
    await waitFor(() => screen.getByText(/Transaction History/i));

    // ✅ Check that Trading tab is active by default
    const tradingTab = screen.getByRole("tab", { name: /Trading/i });
    expect(tradingTab).toHaveAttribute("aria-selected", "true");

    const tradingTable = await screen.findByRole("table", {
      name: /Stock Trading table/i,
    });
    const { getAllByRole, getByText: getByTextInTable } = within(tradingTable);

    // Get all rows in the table body
    const rows = getAllByRole("row");

    // Find the row containing the transaction
    const txnRow = rows.find(
      (row) =>
        row.textContent.includes("Trading") &&
        row.textContent.includes("-SGD 2,000") &&
        row.textContent.includes('Bought AAPL')           
    );

    expect(txnRow).toBeInTheDocument();
    // Check headers exist
    expect(getByTextInTable(/Date/i)).toBeInTheDocument();
    expect(getByTextInTable(/Source/i)).toBeInTheDocument();
    expect(getByTextInTable(/Amount/i)).toBeInTheDocument();
    expect(getByTextInTable(/Desc/i)).toBeInTheDocument();
  });

  test("switches tabs to Dividends", async () => {
    render(<ClientTransactionTable transactionData={mockTransactions} />);

    fireEvent.click(screen.getByRole("tab", { name: /Dividends/i }));

    await waitFor(() => {
      expect(screen.getByText(/\+SGD 50/)).toBeInTheDocument();
    });
  });

  test("search filters transactions by Source", async () => {
    render(<ClientTransactionTable transactionData={mockTransactions} />);

    // ✅ Check that Trading tab is active by default
    const tradingTab = screen.getByRole("tab", { name: /Trading/i });
    expect(tradingTab).toHaveAttribute("aria-selected", "true");

    // Type in the search box
    const searchInput = screen.getByPlaceholderText(
        /Search across all transactions/i
      );
    fireEvent.change(searchInput, { target: { value: "Bank" } });
    fireEvent.click(screen.getByRole("tab", { name: /Wallet/i }));
  

    const tradingTable = await screen.findByRole("table", {
      name: /Wallet Transactions table/i,
    });
    const { getAllByRole, getByText: getByTextInTable } = within(tradingTable);

    // Get all rows in the table body
    const rows = getAllByRole("row");

    // Find the row containing the transaction
    const txnRow = rows.find(
      (row) =>
        row.textContent.includes("Bank") &&
        row.textContent.includes("SGD 5,000") &&
        row.textContent.includes('Initial deposit')           
    );

    expect(txnRow).toBeInTheDocument();
    
  });

  test("shows loading message", () => {
    render(<ClientTransactionTable transactionData={[]} loading={true} />);
    expect(screen.getByText(/Loading.../i)).toBeInTheDocument();
  });

  test("shows empty state when no transactions in a category", () => {
    render(<ClientTransactionTable transactionData={[]} loading={false} />);
    expect(
      screen.getByText(/No trading transactions found/i)
    ).toBeInTheDocument();
  });
});
