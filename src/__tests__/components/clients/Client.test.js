import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import Client from "../../../components/clients/Client";
import { ROUTES } from "../../../routes";
import { getData } from "../../../services/api"; // 👈 import to mock

const mockNavigate = jest.fn();

jest.mock("react-router-dom", () => ({
  ...jest.requireActual("react-router-dom"),
  useNavigate: () => mockNavigate,
}));

jest.mock("../../../services/api", () => ({
  getData: jest.fn(),
}));

describe("Client component", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    getData.mockResolvedValue({
      data: {
        holding: 5000,
        overall_pl: 1000,
        risk_cap: "Medium",
        stop_loss_tolerance: 5,
        sectors: ["Tech"],
      },
    });
  });

  it("navigates when button clicked", async () => {
    render(
      <Client client={{ id: 1, name: "Jane Doe", email: "jane@example.com" }} />
    );
    fireEvent.click(
      await screen.findByRole("button", { name: /view more info/i })
    );
    expect(mockNavigate).toHaveBeenCalledWith(`${ROUTES.RM_CLIENT}/1`);
  });

  it("shows loading state before preferences load", async () => {
    // Simulate slow API by never resolving yet
    getData.mockImplementationOnce(() => new Promise(() => {}));

    render(<Client client={{ id: 1, name: "Jane Doe" }} />);
    expect(screen.getByText(/loading preferences/i)).toBeInTheDocument();
  });

  it("renders preferences after successful fetch", async () => {
    render(<Client client={{ id: 1, name: "Jane Doe" }} />);

    expect(
      await screen.findByText(/current holdings: \$5,000/i)
    ).toBeInTheDocument();
    expect(
      await screen.findByText(/overall p\/l: \$1,000/i)
    ).toBeInTheDocument();
    expect(await screen.findByText(/risk cap: Medium/i)).toBeInTheDocument();
    expect(
      await screen.findByText(/stop loss tolerance: 5%/i)
    ).toBeInTheDocument();
    expect(await screen.findByText(/sectors: Tech/i)).toBeInTheDocument();
  });

  it("renders fallback values when fetch fails", async () => {
    getData.mockRejectedValueOnce(new Error("API down"));
    render(<Client client={{ id: 1, name: "Jane Doe" }} />);

    expect(
      await screen.findByText(/current holdings: NA/i)
    ).toBeInTheDocument();
    expect(await screen.findByText(/overall p\/l: NA/i)).toBeInTheDocument();
    expect(await screen.findByText(/risk cap: NA/i)).toBeInTheDocument();
    expect(
      await screen.findByText(/stop loss tolerance: NA/i)
    ).toBeInTheDocument();
    expect(await screen.findByText(/sectors: NA/i)).toBeInTheDocument();
  });

  it("does not fetch preferences if client id is missing", async () => {
    render(<Client client={{ username: "user123", name: "Jane Doe" }} />);
    await waitFor(() => {
      expect(getData).not.toHaveBeenCalled();
    });
  });
});
