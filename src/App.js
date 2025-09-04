import React from 'react';
import { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import useFetch from './hooks/useFetch';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Navbar from './components/Navbar';
import './styles/App.css';
import ClientCards from './components/clients/ClientCards';
import ClientRecc from './components/clients/ClientRecc';
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
          <Route path="/" element={<ClientCards sx={{ pt: "84px" }} />} />
          <Route path="/client/:id" element={<ClientRecc />} />
        </Routes>
      </main>
    </div>
  );
}

export default App;