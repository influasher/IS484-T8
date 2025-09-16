import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
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

  return (
    <div className="App">
      {/* Sidebar */}
      <Navbar />

      {/* Main Content */}
      <main className="App-content">
        {/* Routes */}
        <Routes>
          <Route path="/EntitiesPage" element={<EntitiesPage />} />
          <Route path="/NewsPage" element={<NewsPage />} />
          <Route path="/IndividualNewsPage/:id" element={<IndividualNewsPage />} />
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