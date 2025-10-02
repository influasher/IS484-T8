import { render, screen, fireEvent, waitFor, act } from "@testing-library/react";
import Client from "../../../components/clients/Client";
import { ROUTES } from "../../../routes";

const mockNavigate = jest.fn();

jest.mock("react-router-dom", () => ({
  ...jest.requireActual("react-router-dom"),
  useNavigate: () => mockNavigate,
}));

describe("Client component", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    global.fetch = jest.fn(() =>
      Promise.resolve({
        ok: true,
        json: () =>
          Promise.resolve({
            data: {
              holding: "AAPL",
              overall_pl: "1000",
              risk_cap: "Medium",
              stop_loss_tolerance: "5%",
              sectors: ["Tech"],
            },
          }),
      })
    );
  });

  it("navigates when button clicked", async () => {
    await act(async () => {
      render(
        <Client client={{ id: 1, name: "Jane Doe", email: "jane@example.com" }} />
      );
    });

    fireEvent.click(screen.getByRole("button", { name: /view more info/i }));
    expect(mockNavigate).toHaveBeenCalledWith(`${ROUTES.RM_CLIENT}/1`);
  });

  it("shows loading state before preferences load", async () => {
    // Override fetch with a delayed response for THIS test only
    global.fetch.mockImplementationOnce(
      () =>
        new Promise((resolve) =>
          setTimeout(
            () =>
              resolve({
                ok: true,
                json: () =>
                  Promise.resolve({
                    data: {
                      holding: "AAPL",
                      overall_pl: "1000",
                      risk_cap: "Medium",
                      stop_loss_tolerance: "5%",
                      sectors: ["Tech"],
                    },
                  }),
              }),
            100 // delay to simulate slow API
          )
        )
    );

    render(<Client client={{ id: 1, name: "Jane Doe" }} />);

    // Immediately visible before fetch resolves
    expect(screen.getByText(/loading preferences/i)).toBeInTheDocument();
  });

  it("renders preferences after successful fetch", async () => {
    await act(async () => {
      render(<Client client={{ id: 1, name: "Jane Doe" }} />);
    });

    expect(await screen.findByText(/current holdings: AAPL/i)).toBeInTheDocument();
    expect(await screen.findByText(/overall p\/l: 1000/i)).toBeInTheDocument();
    expect(await screen.findByText(/risk cap: Medium/i)).toBeInTheDocument();
    expect(await screen.findByText(/stop loss tolerance: 5%/i)).toBeInTheDocument();
    expect(await screen.findByText(/sectors: Tech/i)).toBeInTheDocument();
  });

  it("renders fallback values when fetch fails", async () => {
    global.fetch.mockImplementationOnce(() => Promise.reject(new Error("API down")));

    await act(async () => {
      render(<Client client={{ id: 1, name: "Jane Doe" }} />);
    });

    expect(await screen.findByText(/current holdings: NA/i)).toBeInTheDocument();
    expect(await screen.findByText(/overall p\/l: NA/i)).toBeInTheDocument();
    expect(await screen.findByText(/risk cap: NA/i)).toBeInTheDocument();
    expect(await screen.findByText(/stop loss tolerance: NA/i)).toBeInTheDocument();
    expect(await screen.findByText(/sectors: NA/i)).toBeInTheDocument();
  });

  it("does not fetch preferences if client id is missing", async () => {
    await act(async () => {
      render(<Client client={{ username: "user123", name: "Jane Doe" }} />);
    });

    await waitFor(() => {
      expect(global.fetch).not.toHaveBeenCalled();
    });
  });
});
