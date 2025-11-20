import React from "react";
import {
  render,
  screen,
  fireEvent,
  waitFor,
  within,
} from "@testing-library/react";
import ClientRecc from "../../../components/clients/ClientRecc";
import useFetch from "../../../hooks/useFetch";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import * as api from "../../../services/api";
import useAuth from '../../../hooks/useAuth';

// Mock useFetch
jest.mock("../../../hooks/useFetch");

jest.mock('../../../hooks/useAuth');

beforeEach(() => {
  useAuth.mockReturnValue({
    userRole: 'relationship_manager',
    user: { id: '123', name: 'Test User' },
    token: 'fake-token',
    loading: false,
    isLoggedIn: true,
    login: jest.fn(),
    logout: jest.fn(),
    hasRole: jest.fn(),
    isClient: false,
    isRM: true,
    getUserFullName: jest.fn(),
    isAuthenticated: jest.fn(),
  });
});
// Mock putData API call
jest.spyOn(api, "putData").mockResolvedValue({ success: true });

describe("ClientRecc Component", () => {
  beforeEach(() => {
    // Reset mocks before each test
    jest.clearAllMocks();

    // Mock useFetch implementation
    useFetch.mockImplementation((endpoint) => {
      if (endpoint.includes("/preferences")) {
        return {
          data: {
            data: {
              // ✅ nested structure
              sectors: ["Financials", "Health Care"],
              risk_cap: "Moderate",
              stop_loss_tolerance: -10,
              max_single_position_percent: 15,
              max_sector_allocation_percent: 40,
              min_cash_reserve_percent: 10,
            },
          },
          loading: false,
          error: null,
        };
      }

      if (
        endpoint.includes("/recommendations/client") &&
        !endpoint.includes("/health")
      ) {
        return {
          data: {
            recommendations: [
              {
                entity_id: "1",
                entity_name: "Apple Inc",
                ticker: "AAPL",
                action: "BUY",
                risk_level: "MODERATE",
                sentiment_score: 78.5,
                recommendation_confidence: 0.9,
                reasoning: "Strong growth potential",
                suggested_amount: 5000,
                suggested_allocation_percent: 20,
                current_price: 175.25,
              },
            ],
          },
          loading: false,
          error: null,
        };
      }

      if (endpoint.includes("/health")) {
        return {
          data: { health_data: { overall_health_score: 85 } },
          loading: false,
          error: null,
        };
      }

      // Default: client data
      return {
        data: { data: { id: "123", name: "John Doe" } },
        loading: false,
        error: null,
      };
    });
  });

  const renderComponent = () =>
    render(
      <MemoryRouter initialEntries={["/client/123"]}>
        <Routes>
          <Route path="/client/:id" element={<ClientRecc />} />
        </Routes>
      </MemoryRouter>
    );

  test("renders client name and recommendations", () => {
    renderComponent();

    expect(
      screen.getByText(/Today's Top Recommendations/i)
    ).toBeInTheDocument();
    expect(screen.getByText(/Apple Inc/i)).toBeInTheDocument();
    expect(screen.getByText(/BUY/i)).toBeInTheDocument();
  });

  test("opens edit modal and allows saving changes", async () => {
    renderComponent();

    // Open edit modal
    fireEvent.click(screen.getByLabelText("Edit client"));

    // Modal should be visible
    expect(screen.getByText(/Edit Client Preferences/i)).toBeInTheDocument();

    // Change stop loss tolerance
    await waitFor(() => {
      const dialog = screen.getByRole("dialog");
      expect(dialog).toBeInTheDocument();
    });
    const stopLossInput = within(screen.getByRole("dialog")).getByLabelText(/Stop Loss Tolerance/i);
    fireEvent.change(stopLossInput, { target: { value: -15 } });

    // Click save changes
    fireEvent.click(screen.getByText(/Save Changes/i));

    // Wait for API call
    await waitFor(() => expect(api.putData).toHaveBeenCalled());

    // Optionally, check the updated value passed to API
    expect(api.putData).toHaveBeenCalledWith(
      "/user/123/preferences",
      expect.objectContaining({
        stop_loss_tolerance: -15,
      })
    );
  });

  test("displays health score and risk profile chips", () => {
    renderComponent();

    expect(
      screen.getByText(
        (content) => content.includes("Health Score") && content.includes("85")
      )
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        (content) =>
          content.includes("Risk Profile:") && content.includes("Moderate")
      )
    ).toBeInTheDocument();
  });
});
