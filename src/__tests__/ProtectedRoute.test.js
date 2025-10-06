import React from "react";
import { render, screen } from "@testing-library/react";
import { MemoryRouter, Routes, Route } from "react-router-dom";
import ProtectedRoute from "../components/ProtectedRoute";
import { ROUTES } from "../routes";

// Mock useAuth hook
jest.mock("../hooks/useAuth", () => jest.fn());
import useAuth from "../hooks/useAuth";

const TestComponent = () => <div>Protected Content</div>;

describe("ProtectedRoute", () => {
  afterEach(() => {
    jest.clearAllMocks();
  });

  test("renders loading spinner when loading", () => {
    useAuth.mockReturnValue({
      loading: true,
      isLoggedIn: false,
      userRole: null,
    });

    render(
      <MemoryRouter
        future={{
          v7_startTransition: true,
          v7_relativeSplatPath: true,
        }}
        initialEntries={["/protected"]}
      >
        <Routes>
          <Route
            path="/protected"
            element={
              <ProtectedRoute>
                <TestComponent />
              </ProtectedRoute>
            }
          />
        </Routes>
      </MemoryRouter>
    );

    expect(screen.getByRole("progressbar")).toBeInTheDocument();
  });

  test("redirects to login if not authenticated", () => {
    useAuth.mockReturnValue({
      loading: false,
      isLoggedIn: false,
      userRole: null,
    });

    render(
      <MemoryRouter
        future={{
          v7_startTransition: true,
          v7_relativeSplatPath: true,
        }}
        initialEntries={["/protected"]}
      >
        <Routes>
          <Route
            path="/protected"
            element={
              <ProtectedRoute>
                <TestComponent />
              </ProtectedRoute>
            }
          />
          <Route path={ROUTES.LOGIN} element={<div>Login Page</div>} />
        </Routes>
      </MemoryRouter>
    );

    expect(screen.getByText("Login Page")).toBeInTheDocument();
  });

  test("renders children when authenticated with allowed role", () => {
    useAuth.mockReturnValue({
      loading: false,
      isLoggedIn: true,
      userRole: "client",
    });

    render(
      <MemoryRouter
        future={{
          v7_startTransition: true,
          v7_relativeSplatPath: true,
        }}
        initialEntries={["/protected"]}
      >
        <Routes>
          <Route
            path="/protected"
            element={
              <ProtectedRoute allowedRoles={["client"]}>
                <TestComponent />
              </ProtectedRoute>
            }
          />
        </Routes>
      </MemoryRouter>
    );

    expect(screen.getByText("Protected Content")).toBeInTheDocument();
  });

  test("redirects to client dashboard if wrong role", () => {
    useAuth.mockReturnValue({
      loading: false,
      isLoggedIn: true,
      userRole: "client",
    });

    render(
      <MemoryRouter
        future={{
          v7_startTransition: true,
          v7_relativeSplatPath: true,
        }}
        initialEntries={["/protected"]}
      >
        <Routes>
          <Route
            path="/protected"
            element={
              <ProtectedRoute allowedRoles={["relationship_manager"]}>
                <TestComponent />
              </ProtectedRoute>
            }
          />
          <Route
            path={ROUTES.CLIENT_HOME}
            element={<div>Client Dashboard</div>}
          />
        </Routes>
      </MemoryRouter>
    );

    expect(screen.getByText("Client Dashboard")).toBeInTheDocument();
  });
});