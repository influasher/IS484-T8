jest.mock("axios");
import React from "react";
import { render, screen, fireEvent, act } from "@testing-library/react";
import { renderNavBarWithRouter } from "../test-utils/NavbarTestWrapper";
import useAuth from "../hooks/useAuth";

// Mock logout function
const mockLogout = jest.fn();
jest.mock("../hooks/useAuth", () => ({
  __esModule: true,
  default: () => ({ logout: mockLogout }),
}));

describe("NavBar role-based navigation", () => {
  beforeEach(() => {
    mockLogout.mockClear();
  });

  test("client role: UBS logo navigates to client home", () => {
    render(renderNavBarWithRouter({ role: "client" }));

    fireEvent.click(screen.getByRole("button", { name: /home/i }));
    expect(screen.getByText("Client Home")).toBeInTheDocument();
  });

  test("relationship_manager role: UBS logo navigates to RM home", () => {
    render(renderNavBarWithRouter({ role: "relationship_manager" }));

    fireEvent.click(screen.getByRole("button", { name: /home/i }));
    expect(screen.getByText("RM Home")).toBeInTheDocument();
  });

  test("logout navigates to login for any role", async () => {
    render(renderNavBarWithRouter({ role: "client" }));
  
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: /logout/i }));
    });
  
    expect(mockLogout).toHaveBeenCalled();
    expect(screen.getByText("Login Page")).toBeInTheDocument();
  });

  test("tab navigation works for client role", () => {
    render(renderNavBarWithRouter({ role: "client" }));

    fireEvent.click(screen.getByRole("tab", { name: /news/i }));
    expect(screen.getByText("News Page")).toBeInTheDocument();
  });

  test("tab navigation works for RM role", () => {
    render(renderNavBarWithRouter({ role: "relationship_manager" }));

    fireEvent.click(screen.getByRole("tab", { name: /entities/i }));
    expect(screen.getByText("Entities Page")).toBeInTheDocument();
  });
});
