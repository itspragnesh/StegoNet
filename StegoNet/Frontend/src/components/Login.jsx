import React, { useState } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';

function Login({ setUser, setIsAdmin }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [isAdminLogin, setIsAdminLogin] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const endpoint = isAdminLogin ? '/api/admin-login' : '/api/login';
      const response = await axios.post(`https://stegonet-4.onrender.com${endpoint}`, { username, password });

      if (isAdminLogin) {
        setIsAdmin(true);
        navigate('/admin');
      } else {
        setUser({ username });
        navigate('/dashboard');
      }
    } catch (err) {
      setError(err.response?.data?.error || 'An error occurred');
    }
  };

  return (
    <div className="auth-container">
      <h2>{isAdminLogin ? 'Admin Login' : 'User Login'}</h2>
      <form onSubmit={handleSubmit} className="auth-form">
        <input
          type="text"
          placeholder="Username"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          required
        />
        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />
        <button type="submit">Login</button>
      </form>
      <button
        className="toggle-button"
        onClick={() => {
          setIsAdminLogin(!isAdminLogin);
          setError('');
        }}
      >
        Switch to {isAdminLogin ? 'User' : 'Admin'} Login
      </button>
      {error && <p className="error-message">{error}</p>}
      <p className="switch-text">
        Don't have an account? <a href="/register">Register</a>
      </p>
    </div>
  );
}

export default Login;
