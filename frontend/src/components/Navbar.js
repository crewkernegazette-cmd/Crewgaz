import React, { useContext } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { AuthContext } from '../App';
import { Button } from './ui/button';
import { LogOut, Settings, MessageCircle } from 'lucide-react';

const Navbar = () => {
  const { user, logout } = useContext(AuthContext);
  const location = useLocation();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  const isActive = (path) => location.pathname === path;

  return (
    <nav className="navbar">
      <div className="container">
        <div className="flex items-center justify-between py-4">
          {/* Logo */}
          <Link to="/" className="gazette-logo">
            <div className="gazette-logo-circle"></div>
            <div className="gazette-logo-text">
              The Crewkerne Gazette
            </div>
          </Link>

          {/* Navigation Links */}
          <div className="hidden md:flex items-center space-x-2">
            <Link 
              to="/" 
              className={`nav-link ${isActive('/') ? 'active' : ''}`}
            >
              Home
            </Link>
            <Link 
              to="/news" 
              className={`nav-link ${isActive('/news') ? 'active' : ''}`}
            >
              News
            </Link>
            <Link 
              to="/music" 
              className={`nav-link ${isActive('/music') ? 'active' : ''}`}
            >
              Music
            </Link>
            <Link 
              to="/documentaries" 
              className={`nav-link ${isActive('/documentaries') ? 'active' : ''}`}
            >
              Documentaries
            </Link>
            <Link 
              to="/comedy" 
              className={`nav-link ${isActive('/comedy') ? 'active' : ''}`}
            >
              Comedy
            </Link>
          </div>

          {/* Contact Button & User Actions */}
          <div className="flex items-center space-x-3">
            {/* Prominent Contact Button */}
            <Link to="/contact">
              <Button size="sm" className="bg-red-600 hover:bg-red-700 text-white font-semibold">
                <MessageCircle className="w-4 h-4 mr-2" />
                Contact Us
              </Button>
            </Link>

            {/* User Actions - Only show if logged in */}
            {user && (
              <>
                <Link to="/dashboard">
                  <Button variant="outline" size="sm" className="border-red-600 text-red-400 hover:bg-red-600 hover:text-white">
                    <Settings className="w-4 h-4 mr-2" />
                    Dashboard
                  </Button>
                </Link>
                <Button 
                  variant="outline" 
                  size="sm" 
                  onClick={handleLogout}
                  className="text-red-400 border-red-400 hover:bg-red-400 hover:text-white"
                >
                  <LogOut className="w-4 h-4 mr-2" />
                  Logout
                </Button>
              </>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;