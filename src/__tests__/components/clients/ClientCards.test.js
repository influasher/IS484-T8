import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import ClientCards from "../../../components/clients/ClientCards";
import Client from "../../../components/clients/Client";

// Mock the Client component so we don't need its full implementation
jest.mock("../../../components/clients/Client", () => (props) => (
  <div data-testid="client-card">{props.client.name}</div>
));

// Mock useFetch hook
jest.mock("../../../hooks/useFetch", () => ({
  __esModule: true,
  default: jest.fn(),
}));

describe("ClientCards Component", () => {
  const mockClients = [
    { id: "1", first_name: "John", last_name: "Doe", email: "john@example.com", username: "john.doe", holding: 100, overall_pl: 50, risk_cap: "Medium", sectors: ["Information Technology"] },
    { id: "2", first_name: "Jane", last_name: "Smith", email: "jane@example.com", username: "jane.smith", holding: 200, overall_pl: 150, risk_cap: "High", sectors: ["Financials"] },
  ];

  let useFetch;

  beforeEach(() => {
    useFetch = require("../../../hooks/useFetch").default;
  });

  it("renders loading state", () => {
    useFetch.mockReturnValue({ data: null, loading: true, status: null });
    render(<ClientCards />);
    expect(screen.getByText(/loading clients/i)).toBeInTheDocument();
  });

  it("renders error state", () => {
    useFetch.mockReturnValue({ data: null, loading: false, status: 500 });
    render(<ClientCards />);
    expect(screen.getByText(/failed to load clients/i)).toBeInTheDocument();
  });

  it("renders client cards", () => {
    useFetch.mockReturnValue({ data: mockClients, loading: false, status: 200 });
    render(<ClientCards />);
    mockClients.forEach(client => {
      expect(screen.getByText(`${client.first_name} ${client.last_name}`)).toBeInTheDocument();
    });
  });

  it("opens and closes Add Client dialog", async () => {
    useFetch.mockReturnValue({ data: [], loading: false, status: 200 });
    render(<ClientCards />);
    
    const addButton = screen.getByLabelText(/add client/i);
    fireEvent.click(addButton);

    expect(screen.getByText(/add new client/i)).toBeInTheDocument();

    const cancelButton = screen.getByText(/cancel/i);
    fireEvent.click(cancelButton);

    await waitFor(() => {
      expect(screen.queryByText(/add new client/i)).not.toBeInTheDocument();
    });
  });

  it("allows form input changes", async () => {
    useFetch.mockReturnValue({ data: [], loading: false, status: 200 });
    render(<ClientCards />);
    
    fireEvent.click(screen.getByLabelText(/add client/i));

    const firstNameInput = screen.getByLabelText(/first name/i);
    const lastNameInput = screen.getByLabelText(/last name/i);
    const emailInput = screen.getByLabelText(/email/i);

    fireEvent.change(firstNameInput, { target: { value: "Alice" } });
    fireEvent.change(lastNameInput, { target: { value: "Wonderland" } });
    fireEvent.change(emailInput, { target: { value: "alice@example.com" } });

    expect(firstNameInput.value).toBe("Alice");
    expect(lastNameInput.value).toBe("Wonderland");
    expect(emailInput.value).toBe("alice@example.com");
  });
});
