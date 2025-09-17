import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import Navbar from './components/Navbar';
import LoginPage from './pages/LoginPage';
import NewsPage from './pages/News/NewsPage';
import IndividualNewsPage from './pages/News/IndividualNewsPage';
import EntitiesPage from './pages/Entities/EntitiesPage';
import EntityPage from './pages/Entities/EntityPage';
import DashboardPage from './pages/DashboardPage';
import ClientHomePage from './pages/Clients/ClientHomePage';
import RMHomePage from './pages/RM/RMHomePage';
import RMIndvClientView from './pages/RM/RMIndvClientView';
import SearchTable from './components/ui/SearchTable';
import './styles/App.css';
import { useParams } from 'react-router-dom';

function App() {
  const { id } = useParams(); // Get entity ID from URL

  const location = useLocation();

  // Pages where we don't want a Navbar
  const noNavbarRoutes = ["/Login", "/login"];

  // // Example: role stored in localStorage/session/auth context
  // const role = localStorage.getItem("role"); // "RM" or "Client"

  // // Navbar config
  // const navbarTabs = role === "RM" 
  //   ? ["Dashboard", "Clients", "Entities", "News"]
  //   : ["Dashboard", "Portfolio", "Entities", "News"];

  const showNavbar = !noNavbarRoutes.includes(location.pathname);

  return (
    <div className="App">
       {/* Conditionally render Navbar */}
       {showNavbar && <Navbar />}

      {/* Main Content */}
      <main className="App-content">
        {/* Routes */}
        <Routes>
          <Route path="/EntitiesPage" element={<EntitiesPage />} />
          <Route path="/NewsPage" element={<NewsPage />} />
          <Route path="/IndividualNewsPage" element={<IndividualNewsPage />} />
          <Route path="/Entity/:ticker" element={<EntityPage/>} />
          <Route path="/DashboardPage" element={<DashboardPage />} />
          <Route path="/RM" element={<RMHomePage />} />
          <Route path="/RM/Client/:id" element={<RMIndvClientView/>} />
          <Route path="/Login" element={<LoginPage />} />
          <Route path="/Client" element={<ClientHomePage />} />
          <Route path="Test" element={<SearchTable />} />
          {/* <Route path="*" element={<Navigate to="/Login" replace />} /> */}
        </Routes>
      </main>
    </div>
  );
}

export default App;