import React from 'react';
import { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Navbar from './components/Navbar';
import useFetch from './hooks/useFetch';
import './styles/App.css';
import { useParams } from 'react-router-dom';

function App() {
  const location = useLocation();
  const { id } = useParams(); // Get entity ID from URL
  const [query, setQuery] = React.useState("");

  const url = `/entities/${id}`;
  const { data, loading, error } = useFetch(url);
  const EntityName = data ? data.data.name : "N/A"; // Extract entity name
  const stockID = data ? data.data.id : "N/A"; // Extract stock ID

  
  const handleSearchChange = (val) => {
    setQuery(val);
  };

  const handleSearchSubmit = async (val) => {
    // Example: navigate or fetch
    // navigate(`/search?q=${encodeURIComponent(val)}`);
    console.log("Submitting search:", val);
    // const res = await fetch(`/api/search?q=${encodeURIComponent(val)}`);
    // const data = await res.json();
    // do something with data...
  };

  const handleHomeClick = () => {
    console.log("Home clicked");
    navigate("/");
  };

  const handleProfileClick = () => {
    console.log("Profile clicked");
    // open a menu, navigate("/profile"), etc.
  };

  return (
    <div className="App">
      {/* Sidebar */}
      <Navbar />

      {/* Main Content */}
      <main className="App-content">
        {/* Routes */}
        <Routes>
          <Route path="/" element={<Navigate to="/" />} /> {/* Default route */}
        </Routes>
      </main>'
    </div>
  );
}

export default App;