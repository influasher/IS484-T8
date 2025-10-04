import React from "react";
import {
  BrowserRouter as Router,
  Routes,
  Route,
  Navigate,
  useLocation,
} from "react-router-dom";
import Navbar from "./components/Navbar";
import ProtectedRoute from "./components/ProtectedRoute";
import LoginPage from "./pages/LoginPage";
import NewsPage from "./pages/News/NewsPage";
import IndividualNewsPage from "./pages/News/IndividualNewsPage";
import EntitiesPage from "./pages/Entities/EntitiesPage";
import EntityPage from "./pages/Entities/EntityPage";
import DashboardPage from "./pages/DashboardPage";
import ClientHomePage from "./pages/Clients/ClientHomePage";
import RMHomePage from "./pages/RM/RMHomePage";
import RMIndvClientView from "./pages/RM/RMIndvClientView";
import SearchTable from "./components/ui/SearchTable";
import useAuth from "./hooks/useAuth";
import "./styles/App.css";
import { useParams } from "react-router-dom";
import { ROUTES } from "./routes";

function App() {
  const { id } = useParams(); // Get entity ID from URL

  const location = useLocation();

  // Pages where we don't want a Navbar
  const noNavbarRoutes = ["/Login", "/login"];

  const { userRole } = useAuth();

  const showNavbar = !noNavbarRoutes.includes(location.pathname);

  return (
    <div className="App">
      {/* Conditionally render Navbar */}
      {showNavbar && <Navbar role={userRole} />}

      {/* Main Content */}
      <main className="App-content">
        {/* Routes */}
        <Routes>
          {/* Public route */}
          <Route path={ROUTES.LOGIN} element={<LoginPage />} />

          {/* Protected routes - require authentication */}
          <Route
            path={ROUTES.ENTITIES}
            element={
              <ProtectedRoute>
                <EntitiesPage />
              </ProtectedRoute>
            }
          />
          <Route
            path={ROUTES.NEWS}
            element={
              // <ProtectedRoute>
                <NewsPage />
              // </ProtectedRoute>
            }
          />
          <Route
            path={ROUTES.INDIVIDUAL_NEWS}
            element={
              // <ProtectedRoute>
                <IndividualNewsPage />
              //</ProtectedRoute>
            }
          />
          <Route
            path={`${ROUTES.ENTITY}/:ticker`}
            element={
              <ProtectedRoute>
                <EntityPage />
              </ProtectedRoute>
            }
          />
          <Route
            path={ROUTES.DASHBOARD}
            element={
              <ProtectedRoute>
                <DashboardPage />
              </ProtectedRoute>
            }
          />

          {/* RM-only routes */}
          <Route
            path={ROUTES.RM_HOME}
            element={
              <ProtectedRoute allowedRoles={["relationship_manager"]}>
                <RMHomePage />
              </ProtectedRoute>
            }
          />
          <Route
            path={`${ROUTES.RM_CLIENT}/:id`}
            element={
              <ProtectedRoute allowedRoles={["relationship_manager"]}>
                <RMIndvClientView />
              </ProtectedRoute>
            }
          />

          {/* Client-only routes */}
          <Route
            path={ROUTES.CLIENT_HOME}
            element={
              <ProtectedRoute allowedRoles={["client"]}>
                <ClientHomePage />
              </ProtectedRoute>
            }
          />

          {/* Test route - protected but accessible to all authenticated users */}
          <Route
            path={ROUTES.TEST}
            element={
              <ProtectedRoute>
                <SearchTable />
              </ProtectedRoute>
            }
          />

          {/* Redirect root to login */}
          <Route path="/" element={<Navigate to={ROUTES.LOGIN} replace />} />

          {/* Catch all - redirect to login */}
          <Route path="*" element={<Navigate to={ROUTES.LOGIN} replace />} />
        </Routes>
      </main>
    </div>
  );
}

export default App;
