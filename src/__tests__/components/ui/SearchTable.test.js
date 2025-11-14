import React from "react";
import { render, screen, fireEvent, within } from "@testing-library/react";
import SearchTable from "../../../components/ui/SearchTable";

describe("SearchTable Component", () => {
  const mockData = [
    { id: 1, name: "Item 1" },
    { id: 2, name: "Item 2" },
  ];

  const mockRenderTableBody = (data) => (
    <tbody>
      {data.map((item) => (
        <tr key={item.id}>
          <td>{item.name}</td>
        </tr>
      ))}
    </tbody>
  );

  test("shows default message if renderTableBody not provided", () => {
    render(<SearchTable data={mockData} />);

    // Use getAllByText since there may be multiple rows
    const messages = screen.getAllByText(/no custom table body provided/i);
    expect(messages.length).toBeGreaterThan(0);
  });

  test("renders custom table body when provided", () => {
    render(<SearchTable data={mockData} renderTableBody={mockRenderTableBody} />);

    mockData.forEach((item) => {
      expect(screen.getByText(item.name)).toBeInTheDocument();
    });

    // Default message should NOT appear
    const defaultMessages = screen.queryByText(/no custom table body provided/i);
    expect(defaultMessages).not.toBeInTheDocument();
  });

  test("calls onSearchChange when typing in search input", () => {
    const onSearchChange = jest.fn();
    render(<SearchTable data={mockData} onSearchChange={onSearchChange} />);

    const searchInput = screen.getByPlaceholderText(/search/i);
    fireEvent.change(searchInput, { target: { value: "Test" } });

    expect(onSearchChange).toHaveBeenCalledWith("Test");
  });

  test("calls onSortChange when selecting sort option", () => {
    const onSortChange = jest.fn();
    const sortOptions = [
      { value: "asc", label: "Ascending" },
      { value: "desc", label: "Descending" },
    ];

    render(
      <SearchTable
        data={mockData}
        sortOptions={sortOptions}
        onSortChange={onSortChange}
      />
    );

    const sortSelect = screen.getByLabelText(/sort by/i);
    fireEvent.mouseDown(sortSelect); // open dropdown
    const option = screen.getByText("Ascending");
    fireEvent.click(option);

    expect(onSortChange).toHaveBeenCalledWith("asc");
  });

  test("calls onPageChange when clicking pagination", () => {
    const onPageChange = jest.fn();
    render(
      <SearchTable
        data={mockData}
        totalPages={3}
        currentPage={1}
        onPageChange={onPageChange}
      />
    );

    const pagination = screen.getByRole("navigation"); // MUI Pagination
    const nextPage = within(pagination).getByText("2");
    fireEvent.click(nextPage);

    expect(onPageChange).toHaveBeenCalled();
  });

  test("shows loading message when loading is true", () => {
    render(<SearchTable data={[]} loading={true} />);

    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });
});
