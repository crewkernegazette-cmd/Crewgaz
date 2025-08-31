import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { HelmetProvider } from 'react-helmet-async';
import axios from 'axios';
import './App.css';

// Components
import Navbar from './components/Navbar';
import Footer from './components/Footer';
import Homepage from './components/Homepage';
import NewsSection from './components/NewsSection';
import MusicSection from './components/MusicSection';
import DocumentariesSection from './components/DocumentariesSection';
import ComedySection from './components/ComedySection';
import ContactSection from './components/ContactSection';
import ArticleDetail from './components/ArticleDetail';
import Dashboard from './components/Dashboard';
import LoginForm from './components/LoginForm';
import Debug from './components/Debug';
import { Toaster } from './components/ui/sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = BACKEND_URL;

// Auth Context
export const AuthContext = React.createContext();

function App() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // Configure axios defaults
  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      // Set user from stored token info
      const userData = {
        username: 'admin',  // We'll get this from a proper auth check later
        role: 'admin',
        token: token
      };
      setUser(userData);
    }
    setLoading(false);
  }, []);



  const login = async (credentials) => {
    console.log('Submitting login:', { username: credentials.username });
    
    try {
      const response = await axios.post(`${API}/auth/login`, credentials, {
        headers: {
          'Content-Type': 'application/json'
        }
      });
      
      console.log('Login response received:', response.status, response.data);
      
      const { access_token, role } = response.data;
      
      // Store token and set up authentication
      localStorage.setItem('access_token', access_token);
      axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
      
      // Create user object from response data
      const userData = {
        username: credentials.username,
        role: role,
        token: access_token
      };
      
      setUser(userData);
      console.log('Login successful, user set:', userData);
      
      return { success: true };
    } catch (error) {
      console.error('Login error:', error.response?.data || error.message);
      
      return { 
        success: false, 
        error: error.response?.data?.detail || 'Invalid credentials' 
      };
    }
  };

  const logout = () => {
    localStorage.removeItem('access_token');
    delete axios.defaults.headers.common['Authorization'];
    setUser(null);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center">
        <div className="loading-spinner"></div>
      </div>
    );
  }

  return (
    <HelmetProvider>
      <AuthContext.Provider value={{ user, login, logout }}>
        <div className="App">
          <Router>
            <Navbar />
            <Routes>
              <Route path="/" element={<Homepage />} />
              <Route path="/news" element={<NewsSection />} />
              <Route path="/music" element={<MusicSection />} />
              <Route path="/documentaries" element={<DocumentariesSection />} />
              <Route path="/comedy" element={<ComedySection />} />
              <Route path="/contact" element={<ContactSection />} />
              <Route path="/article/:slug" element={<ArticleDetail />} />
              <Route 
                path="/login" 
                element={user ? <Navigate to="/dashboard" /> : <LoginForm />} 
              />
              <Route 
                path="/dashboard/*" 
                element={user ? <Dashboard /> : <Navigate to="/login" />} 
              />
              <Route path="/debug" element={<Debug />} />
            </Routes>
            <Footer />
            <Toaster />
          </Router>
        </div>
      </AuthContext.Provider>
    </HelmetProvider>
  );
}

export default App;