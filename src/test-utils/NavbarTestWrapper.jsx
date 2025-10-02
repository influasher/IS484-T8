import React from "react";
import { MemoryRouter, Routes, Route } from "react-router-dom";
import { ROUTES } from "../routes";
import NavBar from "../components/Navbar";

// Dummy pages for navigation
const DummyPage = ({ text }) => <div>{text}</div>;

/**
 * Wraps NavBar in a MemoryRouter with dummy routes for testing navigation
 * @param {Object} options
 *   - initialRoute: starting route
 *   - role: "client" or "relationship_manager"
 *   - baseTabs: optional custom tabs for role-specific testing
 */
export const renderNavBarWithRouter = ({
  initialRoute = ROUTES.DASHBOARD,
  role = "client",
  baseTabs = null,
} = {}) => {
  // If no custom tabs, define default tabs
  const tabs = baseTabs || [
    { label: "Entities", path: ROUTES.ENTITIES },
    { label: "News", path: ROUTES.NEWS },
    { label: "Dashboard", path: ROUTES.DASHBOARD },
  ];

  return (
    <MemoryRouter initialEntries={[initialRoute]}>
      <NavBar role={role} />
      <Routes>
        <Route
          path={ROUTES.CLIENT_HOME}
          element={<DummyPage text="Client Home" />}
        />
        <Route path={ROUTES.RM_HOME} element={<DummyPage text="RM Home" />} />
        <Route path={ROUTES.LOGIN} element={<DummyPage text="Login Page" />} />
        <Route
          path={ROUTES.DASHBOARD}
          element={<DummyPage text="Dashboard Page" />}
        />
        <Route path={ROUTES.NEWS} element={<DummyPage text="News Page" />} />
        <Route
          path={ROUTES.ENTITIES}
          element={<DummyPage text="Entities Page" />}
        />
      </Routes>
    </MemoryRouter>
  );
};
