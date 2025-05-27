import React, { useState } from 'react';
import { BrowserRouter as Router, Route, Routes, Navigate } from 'react-router-dom';
import Login from './components/Login';
import Register from './components/Register';
import Admin from './components/Admin';
import UserDashboard from './components/UserDashboard';
import './App.css';

function App() {
  const [user, setUser] = useState(null);
  const [isAdmin, setIsAdmin] = useState(false);

  const handleLogout = () => {
    setUser(null);
    setIsAdmin(false);
  };

  return (
    <Router>
      <div className="App">
        <h1>🔒 Stego Image Sharing App</h1>
        <Routes>
          <Route path="/login" element={<Login setUser={setUser} setIsAdmin={setIsAdmin} />} />
          <Route path="/register" element={<Register />} />
          <Route
            path="/dashboard"
            element={user ? <UserDashboard user={user} handleLogout={handleLogout} /> : <Navigate to="/login" />}
          />
          <Route
            path="/admin"
            element={isAdmin ? <Admin handleLogout={handleLogout} /> : <Navigate to="/login" />}
          />
          <Route path="/" element={<Navigate to="/login" />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;