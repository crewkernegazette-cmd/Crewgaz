import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Clock, Eye } from 'lucide-react';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import TopRail from './TopRail';
import NewsSection from './NewsSection';
import MusicSection from './MusicSection';
import DocumentariesSection from './DocumentariesSection';
import ComedySection from './ComedySection';
import ContactSection from './ContactSection';
import axios from 'axios';

import { API_BASE } from '../config/api';

const Homepage = () => {
  const [breakingNews, setBreakingNews] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showBanner, setShowBanner] = useState(true);

  useEffect(() => {
    fetchBreakingNews();
    fetchPublicSettings();
  }, []);

  const fetchPublicSettings = async () => {
    try {
      const response = await axios.get(`${API_BASE}/api/settings/public`, {
        withCredentials: true
      });
      setShowBanner(response.data?.show_breaking_news_banner || true);
    } catch (error) {
      console.error('Error fetching public settings:', error);
      // Default to showing banner if error
      setShowBanner(true);
    }
  };

  const fetchBreakingNews = async () => {
    try {
      const response = await axios.get(`${API_BASE}/api/articles?is_breaking=true&limit=3`, {
        withCredentials: true
      });
      const breakingData = Array.isArray(response.data) ? response.data : [];
      setBreakingNews(breakingData);
      console.warn('Breaking news state:', breakingData);
    } catch (error) {
      console.error('Error fetching breaking news:', error);
      setBreakingNews([]); // Ensure it's always an array
      console.warn('Breaking news state set to empty array due to error');
    }
    setLoading(false); // Always set loading to false
  };

  const getCategoryBadgeClass = (category) => {
    switch (category) {
      case 'news': return 'category-news';
      case 'music': return 'category-music';
      case 'documentaries': return 'category-documentaries';
      case 'comedy': return 'category-comedy';
      default: return 'category-news';
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    });
  };

  const renderCategoryLabels = (labels) => {
    if (!Array.isArray(labels) || labels.length === 0) return null;
    
    return (
      <div className="flex flex-wrap gap-1 mb-2">
        {labels.slice(0, 2).map((label, index) => (
          <Badge 
            key={index} 
            className="bg-red-600/20 text-red-300 border border-red-600/30 text-xs px-2 py-1"
          >
            {label}
          </Badge>
        ))}
        {labels.length > 2 && (
          <Badge className="bg-slate-600/20 text-slate-300 border border-slate-600/30 text-xs px-2 py-1">
            +{labels.length - 2}
          </Badge>
        )}
      </div>
    );
  };

  // Debug logging in render
  console.warn('Homepage render - Articles state:', articles, 'Type:', typeof articles, 'IsArray:', Array.isArray(articles));
  console.warn('Homepage render - Breaking news state:', breakingNews, 'Type:', typeof breakingNews, 'IsArray:', Array.isArray(breakingNews));

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center">
        <div className="text-white text-xl">Loading...</div>
      </div>
    );
  }

  return (
    <div>
      {/* Breaking News Ticker */}
      {Array.isArray(breakingNews) && breakingNews.length > 0 && showBanner && (
        <div className="bg-red-600 text-white py-2">
          <div className="container mx-auto px-4 flex items-center">
            <span className="bg-red-800 px-3 py-1 text-sm font-bold mr-4">BREAKING</span>
            <div className="flex-1 overflow-hidden">
              <div className="whitespace-nowrap animate-scroll">
                {breakingNews.map((news, index) => (
                  <Link key={news.id || index} to={`/article/${news.slug || news.id}`} className="hover:underline mr-8">
                    {news.title}
                  </Link>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* GB News Style Top Rail */}
      <TopRail />

      {/* News Section */}
      <NewsSection />

      {/* Music Section */}
      <MusicSection />

      {/* Documentaries Section */}
      <DocumentariesSection />

      {/* Comedy Section */}
      <ComedySection />

      {/* Contact Section */}
      <ContactSection />
    </div>
  );
};

export default Homepage;