import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import News from "../../../components/news/News";
import useFetch from "../../../hooks/useFetch";

// Mock react-router-dom Link
jest.mock("react-router-dom", () => ({
  ...jest.requireActual("react-router-dom"),
  Link: ({ children }) => <span>{children}</span>,
}));

// Mock SearchTable
jest.mock("../../../components/ui/SearchTable", () => (props) => {
  if (props.loading) return <div>Loading...</div>;

  return (
    <div data-testid="mock-search-table">
      <input
        placeholder={props.searchPlaceholder}
        value={props.searchTerm}
        onChange={(e) =>
          props.onSearchChange && props.onSearchChange(e.target.value)
        }
      />
      <button
        data-testid="sort-button"
        onClick={() =>
          props.onSortChange && props.onSortChange("sentiment-high")
        }
      >
        Sort
      </button>
      <tbody>
        {props.data &&
          props.data.map((item, i) => (
            <tr key={i}>
              <td>{item.title}</td>
            </tr>
          ))}
      </tbody>
    </div>
  );
});

// Mock useFetch
jest.mock("../../../hooks/useFetch");

describe("News Component", () => {
  const mockData = {
    data: {
      news: [
        { id: 1, title: "News Title 1", publisher: "Publisher 1", published_date: "2025-10-01" },
        { id: 2, title: "News Title 2", publisher: "Publisher 2", published_date: "2025-10-02" },
      ],
      pages: 2,
    },
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  test("renders news data", () => {
    useFetch.mockReturnValue({ data: mockData, loading: false, error: null });

    render(<News />);

    expect(screen.getByText("News Title 1")).toBeInTheDocument();
    expect(screen.getByText("News Title 2")).toBeInTheDocument();
  });

  test("handles search input change", () => {
    useFetch.mockReturnValue({ data: mockData, loading: false, error: null });

    render(<News />);

    const searchInput = screen.getByPlaceholderText(
      /Search news by title, publisher, or content/i
    );
    fireEvent.change(searchInput, { target: { value: "Title 1" } });

    expect(searchInput.value).toBe("Title 1");
  });

  test("handles sort change", () => {
    useFetch.mockReturnValue({ data: mockData, loading: false, error: null });

    render(<News />);

    const sortButton = screen.getByTestId("sort-button");
    fireEvent.click(sortButton);

    // Your News component sets sortOrder state internally.
    // You can test if the sort change triggers the mock callback
    // Optionally, you can spy on setState if needed.
  });

  test("shows loading state", () => {
    useFetch.mockReturnValue({ data: null, loading: true, error: null });

    render(<News />);
    expect(screen.getByText(/Loading/i)).toBeInTheDocument();
  });

//   test("shows error state", () => {
//     useFetch.mockReturnValue({ data: null, loading: false, error: "API Error" });

//     render(<News />);
//     expect(screen.getByText(/Error: API Error/i)).toBeInTheDocument();
//   });
});
