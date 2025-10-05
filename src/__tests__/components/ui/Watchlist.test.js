import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import StockWatchlist from "../../../components/ui/Watchlist";
import useFetch from "../../../hooks/useFetch";
import { MemoryRouter } from "react-router-dom";

// Mock useNavigate
const mockNavigate = jest.fn();
jest.mock("react-router-dom", () => ({
  ...jest.requireActual("react-router-dom"),
  useNavigate: () => mockNavigate,
}));

// Mock useFetch
jest.mock("../../../hooks/useFetch");

describe("StockWatchlist Component", () => {
  const mockStocks = {
    data: [
      { ticker: "AAPL", name: "Apple" },
      { ticker: "TSLA", name: "Tesla" },
    ],
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  test("renders loading state", () => {
    useFetch.mockReturnValue({ data: null, loading: true, error: null });
    render(
      <MemoryRouter>
        <StockWatchlist />
      </MemoryRouter>
    );
    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });

  test("renders error state", () => {
    useFetch.mockReturnValue({ data: null, loading: false, error: "API Error" });
    render(
      <MemoryRouter>
        <StockWatchlist />
      </MemoryRouter>
    );
    expect(screen.getByText(/error: api error/i)).toBeInTheDocument();
  });

  test("renders stocks table after fetching data", () => {
    useFetch.mockReturnValue({ data: mockStocks, loading: false, error: null });
    render(
      <MemoryRouter>
        <StockWatchlist />
      </MemoryRouter>
    );

    // Check that tickers and company names are rendered
    expect(screen.getByText("AAPL")).toBeInTheDocument();
    expect(screen.getByText("Apple")).toBeInTheDocument();
    expect(screen.getByText("TSLA")).toBeInTheDocument();
    expect(screen.getByText("Tesla")).toBeInTheDocument();
  });

  test("filters stocks based on search input", () => {
    useFetch.mockReturnValue({ data: mockStocks, loading: false, error: null });
    render(
      <MemoryRouter>
        <StockWatchlist />
      </MemoryRouter>
    );

    const searchInput = screen.getByPlaceholderText(/search by company name or ticker/i);
    fireEvent.change(searchInput, { target: { value: "Apple" } });

    expect(screen.getByText("Apple")).toBeInTheDocument();
    expect(screen.queryByText("Tesla")).not.toBeInTheDocument();
  });

  test("shows message if no stocks match search", () => {
    useFetch.mockReturnValue({ data: mockStocks, loading: false, error: null });
    render(
      <MemoryRouter>
        <StockWatchlist />
      </MemoryRouter>
    );

    const searchInput = screen.getByPlaceholderText(/search by company name or ticker/i);
    fireEvent.change(searchInput, { target: { value: "Nonexistent" } });

    expect(screen.getByText(/no stocks found matching "Nonexistent"/i)).toBeInTheDocument();
  });

  test("navigates to entity page on row click", () => {
    useFetch.mockReturnValue({ data: mockStocks, loading: false, error: null });
    render(
      <MemoryRouter>
        <StockWatchlist />
      </MemoryRouter>
    );

    const appleRow = screen.getByText("AAPL").closest("tr");
    fireEvent.click(appleRow);

    expect(mockNavigate).toHaveBeenCalledWith("/Entity/AAPL"); // Adjust route if needed
  });
});
