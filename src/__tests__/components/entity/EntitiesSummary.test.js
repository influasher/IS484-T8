// Entities.test.jsx
import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import Entities from "../../../components/entity/EntitiesSummary";
import useFetch from "../../../hooks/useFetch";
import { MemoryRouter } from "react-router-dom";

// Mock useFetch
jest.mock("../../../hooks/useFetch");

// Mock SearchTable
jest.mock("../../../components/ui/SearchTable", () => (props) => {
  return (
    <div>
      {props.loading && <div>Loading...</div>}
      {!props.loading && !props.error && (
        <div>
          Data loaded
          {/* Expose props functions for testing */}
          <button onClick={() => props.onPageChange(null, 2)}>Next Page</button>
          <input
            placeholder={props.searchPlaceholder}
            value={props.searchTerm}
            onChange={(e) => props.onSearchChange(e.target.value)}
          />
        </div>
      )}
    </div>
  );
});

describe("Entities Component", () => {
  const mockData = {
    data: {
      entities: [
        {
          ticker: "AAPL",
          name: "Apple Inc.",
          summary: "Tech company",
          sentiment_score: 0.8,
          classification: "positive",
        },
        {
          ticker: "TSLA",
          name: "Tesla Inc.",
          summary: "Electric cars",
          sentiment_score: -0.2,
          classification: "negative",
        },
      ],
      pages: 1,
    },
  };

  it("shows loading state initially", () => {
    useFetch.mockReturnValue({ data: null, loading: true, error: null });
    render(
      <MemoryRouter>
        <Entities />
      </MemoryRouter>
    );

    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });

//   it("shows error message if fetch fails", () => {
//     useFetch.mockReturnValue({ data: null, loading: false, error: "API error" });
//     render(
//       <MemoryRouter>
//         <Entities />
//       </MemoryRouter>
//     );

//     expect(screen.getByText(/api error/i)).toBeInTheDocument();
//   });

  it("renders entity data correctly", () => {
    useFetch.mockReturnValue({ data: mockData, loading: false, error: null });
    render(
      <MemoryRouter>
        <Entities />
      </MemoryRouter>
    );

    expect(screen.getByText(/data loaded/i)).toBeInTheDocument();
  });

  it("calls onPageChange when pagination button is clicked", () => {
    useFetch.mockReturnValue({ data: mockData, loading: false, error: null });
    render(
      <MemoryRouter>
        <Entities />
      </MemoryRouter>
    );

    const nextButton = screen.getByText(/next page/i);
    fireEvent.click(nextButton);
    // You could spy on setCurrentPage in a more advanced setup
  });

  it("updates search term when typing in search box", () => {
    useFetch.mockReturnValue({ data: mockData, loading: false, error: null });
    render(
      <MemoryRouter>
        <Entities />
      </MemoryRouter>
    );

    const searchInput = screen.getByPlaceholderText(/search entities by name/i);
    fireEvent.change(searchInput, { target: { value: "Tesla" } });

    expect(searchInput.value).toBe("Tesla");
  });
});
