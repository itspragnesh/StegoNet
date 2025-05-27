import React, { useState, useEffect } from 'react';
import axios from 'axios';

function Admin({ handleLogout }) {
  const [users, setUsers] = useState([]);
  const [messages, setMessages] = useState([]);
  const [message, setMessage] = useState('');

  useEffect(() => {
    const fetchUsers = async () => {
      const response = await axios.get('http://localhost:5000/api/users');
      setUsers(response.data.filter(u => u !== 'admin'));
    };
    const fetchMessages = async () => {
      const response = await axios.get('http://localhost:5000/api/all-messages');
      setMessages(response.data);
    };
    fetchUsers();
    fetchMessages();
  }, []);

  const handleRemoveUser = async (username) => {
    try {
      await axios.delete(`http://localhost:5000/api/remove-user/${username}`);
      setUsers(users.filter(u => u !== username));
      setMessages(messages.filter(m => m.sender !== username && m.receiver !== username));
      setMessage(`User ${username} removed!`);
      setTimeout(() => setMessage(''), 3000);
    } catch (err) {
      setMessage('Error removing user');
    }
  };

  const handleRemoveImage = async (msgId) => {
    try {
      await axios.delete(`http://localhost:5000/api/delete-image/${msgId}`);
      setMessages(messages.filter(m => m.id !== msgId));
      setMessage(`Image ${msgId} removed!`);
      setTimeout(() => setMessage(''), 3000);
    } catch (err) {
      setMessage('Error removing image');
    }
  };

  return (
    <div>
      <h2>Admin Dashboard</h2>
      <button onClick={handleLogout}>Logout</button>
      {message && <p style={{ color: message.includes('Error') ? 'red' : 'green' }}>{message}</p>}
      <h3>Registered Users</h3>
      {users.map(user => (
        <div key={user} style={{ display: 'flex', justifyContent: 'space-between', margin: '10px 0' }}>
          <span>{user}</span>
          <button onClick={() => handleRemoveUser(user)}>Remove</button>
        </div>
      ))}
      <h3>All Messages</h3>
      {messages.map(msg => (
        <div key={msg.id} style={{ display: 'flex', justifyContent: 'space-between', margin: '10px 0' }}>
          <span>ID: {msg.id}, Sender: {msg.sender}, Receiver: {msg.receiver}</span>
          <button onClick={() => handleRemoveImage(msg.id)}>Remove</button>
        </div>
      ))}
    </div>
  );
}

export default Admin;