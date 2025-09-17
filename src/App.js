import React from "react";
import {
  BrowserRouter as Router,
  Routes,
  Route,
  Navigate,
  useLocation,
} from "react-router-dom";
import Navbar from "./components/Navbar";
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
import "./styles/App.css";
import { useParams } from "react-router-dom";
import { ROUTES } from "./routes";

function App() {
  const { id } = useParams(); // Get entity ID from URL

  const location = useLocation();

  // Pages where we don't want a Navbar
  const noNavbarRoutes = ["/Login", "/login"];

  // Example: role stored in localStorage/session/auth context
  const role = "RM"; // "RM" or "Client"

  const showNavbar = !noNavbarRoutes.includes(location.pathname);

  return (
    <div className="App">
      {/* Conditionally render Navbar */}
      {showNavbar && <Navbar role={role} />}

      {/* Main Content */}
      <main className="App-content">
        {/* Routes */}
        <Routes>
          <Route path={ROUTES.ENTITIES} element={<EntitiesPage />} />
          <Route path={ROUTES.NEWS} element={<NewsPage />} />
          <Route
            path={ROUTES.INDIVIDUAL_NEWS}
            element={<IndividualNewsPage />}
          />
          <Route path={`${ROUTES.ENTITY}/:ticker`} element={<EntityPage />} />
          <Route path={ROUTES.DASHBOARD} element={<DashboardPage />} />
          <Route path={ROUTES.RM_HOME} element={<RMHomePage />} />
          <Route path={`${ROUTES.RM_CLIENT}/:id`} element={<RMIndvClientView />} />
          <Route path={ROUTES.LOGIN} element={<LoginPage />} />
          <Route path={ROUTES.CLIENT_HOME} element={<ClientHomePage />} />
          <Route path={ROUTES.TEST} element={<SearchTable />} />
          {/* <Route path="*" element={<Navigate to="/Login" replace />} /> */}
        </Routes>
      </main>
    </div>
  );
}

export default App;
