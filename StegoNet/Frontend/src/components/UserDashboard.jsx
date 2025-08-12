import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Tab, Tabs, TabList, TabPanel } from 'react-tabs';
import 'react-tabs/style/react-tabs.css';

function UserDashboard({ user, handleLogout }) {
  const [users, setUsers] = useState([]);
  const [receiver, setReceiver] = useState('');
  const [coverImage, setCoverImage] = useState(null);
  const [secretImage, setSecretImage] = useState(null);
  const [stegoImage, setStegoImage] = useState(null);
  const [receivedImages, setReceivedImages] = useState([]);
  const [message, setMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    const fetchUsers = async () => {
      try {
        const response = await axios.get('https://stegonet-4.onrender.com/api/users');
        setUsers(response.data.filter(u => u !== user.username));
      } catch (err) {
        setMessage('Error fetching users: ' + (err.response?.data?.error || err.message));
      }
    };
    const fetchReceivedImages = async () => {
      try {
        const response = await axios.get(`https://stegonet-4.onrender.com/api/received-images/${user.username}`);
        setReceivedImages(response.data);
      } catch (err) {
        setMessage('Error fetching received images: ' + (err.response?.data?.error || err.message));
      }
    };
    fetchUsers();
    fetchReceivedImages();
  }, [user.username]);

  const handleSendStego = async (e) => {
    e.preventDefault();
    if (isLoading) return;
    setIsLoading(true);
    setMessage('');

    const formData = new FormData();
    formData.append('sender', user.username);
    formData.append('receiver', receiver);
    formData.append('cover_image', coverImage);
    formData.append('secret_image', secretImage);

    try {
      console.log('Sending stego image with:', { sender: user.username, receiver, coverImage, secretImage });
      const response = await axios.post('https://stegonet-4.onrender.com/api/send-stego', formData);
      setStegoImage(response.data.stego_image);
      setMessage(response.data.message);
      setTimeout(() => setMessage(''), 5000);
      const updatedImages = await axios.get(`https://stegonet-4.onrender.com/api/received-images/${user.username}`);
      setReceivedImages(updatedImages.data);
    } catch (err) {
      console.error('Error sending stego image:', err.response?.data);
      setMessage(`Error sending stego image: ${err.response?.data?.error || err.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleExtractSecret = async (msgId) => {
    if (isLoading) return;
    setIsLoading(true);
    setMessage('');

    try {
      const response = await axios.get(`https://stegonet-4.onrender.com/api/extract-secret/${msgId}`);
      const link = document.createElement('a');
      link.href = `data:image/png;base64,${response.data.secret_image}`;
      link.download = 'secret_image.png';
      link.click();
      setMessage(response.data.message);
      setTimeout(() => setMessage(''), 5000);
    } catch (err) {
      console.error('Error extracting secret:', err.response?.data);
      setMessage(`Error extracting secret: ${err.response?.data?.error || err.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDeleteImage = async (msgId) => {
    if (isLoading) return;
    setIsLoading(true);
    setMessage('');

    try {
      await axios.delete(`https://stegonet-4.onrender.com/api/delete-image/${msgId}`);
      setReceivedImages(receivedImages.filter(img => img.id !== msgId));
      setMessage('Image deleted successfully!');
      setTimeout(() => setMessage(''), 3000);
    } catch (err) {
      console.error('Error deleting image:', err.response?.data);
      setMessage(`Error deleting image: ${err.response?.data?.error || err.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div>
      <h2>Welcome, {user.username}</h2>
      <button onClick={handleLogout} disabled={isLoading}>Logout</button>
      {message && <p style={{ color: message.includes('Error') ? 'red' : 'green' }}>{message}</p>}
      
      <Tabs>
        <TabList>
          <Tab>Send Stego Image</Tab>
          <Tab>Received Stego Images</Tab>
        </TabList>

        <TabPanel>
          <h3>Send Stego Image</h3>
          <form onSubmit={handleSendStego}>
            <select value={receiver} onChange={(e) => setReceiver(e.target.value)} required disabled={isLoading}>
              <option value="">Select Receiver</option>
              {users.map(u => <option key={u} value={u}>{u}</option>)}
            </select>
            <div style={{ display: 'flex', justifyContent: 'space-around' }}>
              <div>
                <h4>Cover Image</h4>
                <input
                  type="file"
                  accept="image/*"
                  onChange={(e) => setCoverImage(e.target.files[0])}
                  required
                  disabled={isLoading}
                />
                {coverImage && <img src={URL.createObjectURL(coverImage)} alt="Cover" />}
              </div>
              <div>
                <h4>Secret Image</h4>
                <input
                  type="file"
                  accept="image/*"
                  onChange={(e) => setSecretImage(e.target.files[0])}
                  required
                  disabled={isLoading}
                />
                {secretImage && <img src={URL.createObjectURL(secretImage)} alt="Secret" />}
              </div>
            </div>
            <button type="submit" disabled={isLoading}>
              {isLoading ? 'Processing...' : 'Send Stego Image'}
            </button>
          </form>
          {stegoImage && <img src={`data:image/png;base64,${stegoImage}`} alt="Stego" />}
        </TabPanel>
        <TabPanel>
          <h3>Received Stego Images</h3>
          {receivedImages.map(img => (
            <div key={img.id}>
              <h4>From: {img.sender}</h4>
              <img src={`data:image/png;base64,${img.stego_image}`} alt="Stego" />
              <button onClick={() => handleExtractSecret(img.id)} disabled={isLoading}>
                {isLoading ? 'Processing...' : 'Extract Secret'}
              </button>
              <button onClick={() => handleDeleteImage(img.id)} disabled={isLoading}>
                Delete Image
              </button>
            </div>
          ))}
        </TabPanel>
      </Tabs>
    </div>
  );
}

export default UserDashboard;
