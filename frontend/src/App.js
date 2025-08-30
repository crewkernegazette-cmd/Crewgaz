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
    const token = localStorage.getItem('token');
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      checkAuth();
    } else {
      setLoading(false);
    }
  }, []);

  const checkAuth = async () => {
    try {
      const response = await axios.get(`${API}/auth/me`);
      setUser(response.data);
    } catch (error) {
      console.error('Auth check failed:', error);
      localStorage.removeItem('token');
      delete axios.defaults.headers.common['Authorization'];
    } finally {
      setLoading(false);
    }
  };

  const login = async (credentials) => {
    try {
      // Try emergency login first (bypasses database issues)
      const response = await axios.post(`${API}/auth/emergency-login`, credentials);
      const { access_token, user: userData } = response.data;
      
      localStorage.setItem('token', access_token);
      axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
      setUser(userData);
      
      return { success: true };
    } catch (error) {
      // If emergency login fails, try regular login
      try {
        const response = await axios.post(`${API}/auth/login`, credentials);
        const { access_token, user: userData } = response.data;
        
        localStorage.setItem('token', access_token);
        axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
        setUser(userData);
        
        return { success: true };
      } catch (error2) {
        return { 
          success: false, 
          error: error2.response?.data?.detail || 'Login failed' 
        };
      }
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
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
              <Route path="/article/:id" element={<ArticleDetail />} />
              <Route 
                path="/login" 
                element={user ? <Navigate to="/dashboard" /> : <LoginForm />} 
              />
              <Route 
                path="/dashboard/*" 
                element={user ? <Dashboard /> : <Navigate to="/login" />} 
              />
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