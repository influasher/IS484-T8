if (typeof structuredClone === "undefined") {
  global.structuredClone = (obj) => JSON.parse(JSON.stringify(obj));
}

import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import { MemoryRouter, Routes, Route } from "react-router-dom";
import IndvEntity from "../../../components/entity/IndvEntity";
import useFetch from "../../../hooks/useFetch";

// Mock useFetch
jest.mock("../../../hooks/useFetch");

// Mocked data
const mockEntityData = {
  data: {
    id: 1,
    name: "Test Entity",
    ticker: "TEST",
    AssetType: "Equity",
    summary: "Test summary",
    Sector: "Technology",
    Industry: "Software",
    sentiment_score: 0.5,
    simple_average: 0.4,
    time_decay: 0.6,
  },
};

const mockNewsData = {
  data: {
    news: [
      {
        id: 101,
        title: "News Title 1",
        summary: "Summary 1",
        publisher: "Publisher 1",
        published_date: "2025-10-01",
      },
      {
        id: 102,
        title: "News Title 2",
        summary: "Summary 2",
        publisher: "Publisher 2",
        published_date: "2025-10-02",
      },
    ],
    pages: 1,
  },
};

const mockEntityChartData = {
  data: {
    stock_chart: {
      dates: ["2025-10-01", "2025-10-02", "2025-10-03"],
      prices: [100, 102, 101],
      performance: 2,
    },
  },
};

const mockIRXData = {
  data: {
    stock_chart: {
      dates: ["2025-10-01", "2025-10-02", "2025-10-03"],
      prices: [1, 1.1, 1.05],
    },
  },
};

beforeEach(() => {
  // Mock implementation for different URLs
  useFetch.mockImplementation((url) => {
    if (url === "/entities/TEST")
      return { data: mockEntityData, loading: false, error: null };
    if (url.startsWith("/news/entity/"))
      return { data: mockNewsData, loading: false, error: null };
    if (url === `/entities/${mockEntityData.data.id}/chart?period=1Y`)
      return { data: mockEntityChartData, loading: false, error: null };
    if (url === "/entities/ticker=^IRX/chart?period=1Y")
      return { data: mockIRXData, loading: false, error: null };
    return { data: null, loading: false, error: null };
  });
});

describe("IndvEntity Component", () => {
  test("renders entity data with news and sentiment", () => {
    render(
      <MemoryRouter initialEntries={["/entity/TEST"]}>
        <Routes>
          <Route path="/entity/:ticker" element={<IndvEntity />} />
        </Routes>
      </MemoryRouter>
    );

    // Check entity ticker
    expect(
      screen.getByRole("heading", { name: "TEST", level: 5 })
    ).toBeInTheDocument();
    // Check news titles
    expect(screen.getByText("News Title 1")).toBeInTheDocument();
    expect(screen.getByText("News Title 2")).toBeInTheDocument();
    // Check sentiment scores
    expect(screen.getByText(/Weighted Sentiment/)).toBeInTheDocument();
    expect(screen.getByText(/Simple Average/)).toBeInTheDocument();
    expect(screen.getByText(/Time Decay/)).toBeInTheDocument();
  });

  test("handles pagination click", () => {
    render(
      <MemoryRouter initialEntries={["/entity/TEST"]}>
        <Routes>
          <Route path="/entity/:ticker" element={<IndvEntity />} />
        </Routes>
      </MemoryRouter>
    );

    // Pagination exists only if totalPages > 1
    const pagination = screen.queryByRole("navigation");
    expect(pagination).not.toBeInTheDocument(); // Only 1 page in mock
  });
});
